"""Tests de T-12b: listado paginado de frases por HTTP (AC-15).

Nivel `tests/api/` (plan §7): `TestClient` con dependencias sustituidas.
`GET /frases` no existe todavía (T-12b sin implementar): la ruta `/api/v1/
frases` ya está registrada para `POST` (T-12a), así que Starlette responde
`405 Method Not Allowed` en vez de `404`. Estos tests fallan hoy por eso, no
por un error de importación.

Para sembrar frases se genera su vector con el mismo `FakeEmbedder` y después
se limpia `embedder.textos_recibidos`, para que el espía solo registre lo que
hace el propio listado (STATUS.md, convención de T-08).
"""

import pytest
from fastapi.testclient import TestClient

from app.domain.entidades import EstadoFrase, FraseNueva
from app.domain.normalizacion import normalizar
from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


def _sembrar_frases(
    repositorio: RepositorioEnMemoria, embedder: FakeEmbedder, cantidad: int
) -> None:
    for indice in range(1, cantidad + 1):
        texto = f"Frase de prueba {indice:02d}"
        repositorio.sembrar(texto, embedder.generar(texto))
    embedder.textos_recibidos.clear()


# --------------------------------------------------------------------------
# AC-15 — Listado paginado y ordenado
# --------------------------------------------------------------------------


def test_ac15_listado_sin_parametros_devuelve_primeros_20_ordenados_por_id_descendente(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    # `RepositorioEnMemoria` asigna fecha fija a todas las frases sembradas
    # (mismo `creada_en`), así que el orden depende del desempate por
    # identificador descendente, igual que en la consulta SQL real.
    _sembrar_frases(repositorio, embedder, 25)

    respuesta = cliente.get("/api/v1/frases")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 25
    assert cuerpo["limite"] == 20
    assert cuerpo["desplazamiento"] == 0
    items = cuerpo["items"]
    assert len(items) == 20
    assert [item["id"] for item in items] == list(range(25, 5, -1))
    primero = items[0]
    assert primero["texto"] == "Frase de prueba 25"
    assert primero["estado"] == "UNICA"
    assert primero["puntaje_similitud"] is None
    assert "creada_en" in primero


def test_ac15_item_del_listado_conserva_el_texto_original_sin_normalizar(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    texto_original = "  El PAGO   fue  RECHAZADO  "
    repositorio.sembrar(texto_original, embedder.generar(texto_original))
    embedder.textos_recibidos.clear()

    respuesta = cliente.get("/api/v1/frases")

    assert respuesta.status_code == 200
    item = respuesta.json()["items"][0]
    assert item["texto"] == texto_original
    assert set(item.keys()) == {
        "id",
        "texto",
        "estado",
        "puntaje_similitud",
        "creada_en",
        "mas_parecida",
    }


def test_ac15_listado_limite_100_desplazamiento_20_devuelve_los_5_restantes(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    _sembrar_frases(repositorio, embedder, 25)

    respuesta = cliente.get("/api/v1/frases", params={"limite": 100, "desplazamiento": 20})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 25
    assert cuerpo["limite"] == 100
    assert cuerpo["desplazamiento"] == 20
    assert [item["id"] for item in cuerpo["items"]] == [5, 4, 3, 2, 1]


def test_ac15_desplazamiento_mayor_que_el_total_devuelve_200_con_lista_vacia(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    # B-22.
    _sembrar_frases(repositorio, embedder, 25)

    respuesta = cliente.get("/api/v1/frases", params={"desplazamiento": 1000})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["items"] == []
    assert cuerpo["total"] == 25


def test_ac15_listado_con_la_base_vacia_devuelve_total_cero_y_items_vacio(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/v1/frases")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 0
    assert cuerpo["items"] == []


@pytest.mark.parametrize(
    ("parametro", "valor"),
    [
        ("limite", "0"),
        ("limite", "101"),
        ("desplazamiento", "-1"),
        ("limite", "abc"),
        # Mayor que BIGINT: PostgreSQL lo rechaza y, sin tope, la API
        # respondería 503 como si la base estuviera caída.
        ("desplazamiento", str(2**63)),
    ],
)
def test_ac15_parametros_de_paginacion_fuera_de_rango_devuelven_422_parametros_invalidos(
    cliente: TestClient, parametro: str, valor: str
) -> None:
    respuesta = cliente.get("/api/v1/frases", params={parametro: valor})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "PARAMETROS_INVALIDOS"
    assert parametro in cuerpo["detalles"]


def test_ac15_listado_no_invoca_al_proveedor_de_embeddings(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    _sembrar_frases(repositorio, embedder, 3)

    respuesta = cliente.get("/api/v1/frases")

    assert respuesta.status_code == 200
    assert embedder.textos_recibidos == []


# --------------------------------------------------------------------------
# AC-19 — El listado incluye la frase más parecida
# --------------------------------------------------------------------------


def test_ac19_elemento_de_duplicado_confirmado_incluye_mas_parecida_con_id_y_texto_original(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    # El texto original de "auto" no está normalizado (mayúsculas y espacios
    # sobrantes) para comprobar que `mas_parecida.texto` es el texto ORIGINAL
    # de la frase referida, no su versión normalizada.
    texto_original_auto = "  Compré un AUTO  "
    auto = repositorio.sembrar(texto_original_auto, embedder.generar(texto_original_auto))

    texto_carro = "Compré un carro"
    carro = repositorio.guardar(
        FraseNueva(
            texto_original=texto_carro,
            texto_normalizado=normalizar(texto_carro),
            embedding=embedder.generar(texto_carro),
            estado=EstadoFrase.DUPLICADO_CONFIRMADO,
            puntaje_similitud=0.95,
            id_mas_parecida=auto.id,
            modelo="modelo-falso",
            umbral_aplicado=0.80,
        )
    )
    embedder.textos_recibidos.clear()

    respuesta = cliente.get("/api/v1/frases")

    assert respuesta.status_code == 200
    items = {item["id"]: item for item in respuesta.json()["items"]}
    assert items[carro.id]["mas_parecida"] == {"id": auto.id, "texto": texto_original_auto}


def test_ac19_elemento_de_la_primera_frase_registrada_incluye_mas_parecida_null(
    cliente: TestClient, repositorio: RepositorioEnMemoria, embedder: FakeEmbedder
) -> None:
    texto = "Compré un auto"
    repositorio.sembrar(texto, embedder.generar(texto))
    embedder.textos_recibidos.clear()

    respuesta = cliente.get("/api/v1/frases")

    assert respuesta.status_code == 200
    item = respuesta.json()["items"][0]
    assert "mas_parecida" in item
    assert item["mas_parecida"] is None
