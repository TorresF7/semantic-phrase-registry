"""Tests de T-12a: validación de entrada por HTTP (AC-01, AC-02, AC-02b).

Nivel `tests/api/` (plan §7): `TestClient` con dependencias sustituidas. Cubre
la frontera HTTP; la lógica de normalización y longitud ya está probada sin
infraestructura en `tests/unit/domain/test_normalizacion.py`.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria

# --------------------------------------------------------------------------
# AC-01 — Frase demasiado corta o vacía
# --------------------------------------------------------------------------


@pytest.mark.parametrize("texto", ["  ", "ab"])
def test_ac01_texto_invalido_al_validar_devuelve_422_frase_invalida_y_no_consulta_nada(
    cliente: TestClient,
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    texto: str,
) -> None:
    # Si el caso de uso llegara a consultar el repositorio pese a la frase
    # inválida, la excepción genérica lo delataría con un 500 en vez de 422.
    repositorio.fallo = RuntimeError("la base no debería consultarse para una frase inválida")

    respuesta = cliente.post("/api/v1/frases/validar", json={"texto": texto})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "FRASE_INVALIDA"
    assert "texto" in cuerpo["detalles"]
    assert embedder.textos_recibidos == []


@pytest.mark.parametrize("texto", ["  ", "ab"])
def test_ac01_texto_invalido_al_guardar_devuelve_422_frase_invalida_y_no_consulta_nada(
    cliente: TestClient,
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    texto: str,
) -> None:
    repositorio.fallo = RuntimeError("la base no debería consultarse para una frase inválida")

    respuesta = cliente.post("/api/v1/frases", json={"texto": texto, "confirmar_duplicado": False})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "FRASE_INVALIDA"
    assert "texto" in cuerpo["detalles"]
    assert embedder.textos_recibidos == []


@pytest.mark.parametrize(
    ("ruta", "cuerpo_extra"),
    [
        ("/api/v1/frases/validar", {}),
        ("/api/v1/frases", {"confirmar_duplicado": False}),
    ],
)
def test_ac01_texto_con_caracter_nulo_devuelve_422_frase_invalida_y_no_consulta_nada_b27(
    cliente: TestClient,
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    ruta: str,
    cuerpo_extra: dict[str, Any],
) -> None:
    # PostgreSQL no admite U+0000 en columnas de texto: si llegara a la base,
    # el driver fallaría. Se rechaza antes, en el dominio (RN-01).
    repositorio.fallo = RuntimeError("la base no debería consultarse para una frase inválida")

    respuesta = cliente.post(ruta, json={"texto": "ab\u0000cd", **cuerpo_extra})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "FRASE_INVALIDA"
    assert "texto" in cuerpo["detalles"]
    assert embedder.textos_recibidos == []


# --------------------------------------------------------------------------
# AC-01 (último «Y», CH-04) — Solo caracteres de formato (Cf), tras
# eliminarlos queda vacío (B-28)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ruta", "cuerpo_extra"),
    [
        ("/api/v1/frases/validar", {}),
        ("/api/v1/frases", {"confirmar_duplicado": False}),
    ],
)
def test_ac01_tres_caracteres_de_formato_normalizan_a_vacio_devuelve_422_frase_invalida_b28(
    cliente: TestClient,
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    ruta: str,
    cuerpo_extra: dict[str, Any],
) -> None:
    # Tres U+200B (categoría Cf) se eliminan al normalizar (CH-04, D-41) y el
    # texto queda vacío: debe rechazarse con el mensaje de longitud mínima, no
    # con el de caracteres no permitidos (ese es para los Cc de D-32).
    repositorio.fallo = RuntimeError("la base no debería consultarse para una frase inválida")

    respuesta = cliente.post(ruta, json={"texto": "\u200b\u200b\u200b", **cuerpo_extra})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "FRASE_INVALIDA"
    assert cuerpo["detalles"]["texto"] == "La frase debe tener al menos 3 caracteres."
    assert embedder.textos_recibidos == []


# --------------------------------------------------------------------------
# AC-02 — Frase demasiado larga
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ruta", "cuerpo_extra"),
    [
        ("/api/v1/frases/validar", {}),
        ("/api/v1/frases", {"confirmar_duplicado": False}),
    ],
)
def test_ac02_texto_de_281_caracteres_normalizados_devuelve_422_y_menciona_el_maximo(
    cliente: TestClient, ruta: str, cuerpo_extra: dict[str, Any]
) -> None:
    texto = "a" * 281

    respuesta = cliente.post(ruta, json={"texto": texto, **cuerpo_extra})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "FRASE_INVALIDA"
    assert "280" in cuerpo["mensaje"]


def test_ac02_texto_de_300_caracteres_que_normaliza_a_250_se_acepta_al_validar(
    cliente: TestClient,
) -> None:
    # 25 espacios + 250 caracteres sin espacios internos + 25 espacios: el
    # recorte de RN-02 deja el texto normalizado en 250 caracteres, aunque el
    # crudo tenga 300. Un `max_length=280` en el schema rechazaría esto, que
    # es exactamente el error que la spec pide evitar.
    texto = " " * 25 + "b" * 250 + " " * 25
    assert len(texto) == 300

    respuesta = cliente.post("/api/v1/frases/validar", json={"texto": texto})

    assert respuesta.status_code == 200


# --------------------------------------------------------------------------
# AC-02b — Cuerpo de la petición mal formado
# --------------------------------------------------------------------------


def test_ac02b_sin_campo_texto_devuelve_422_parametros_invalidos(cliente: TestClient) -> None:
    respuesta = cliente.post("/api/v1/frases/validar", json={})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "PARAMETROS_INVALIDOS"
    assert "mensaje" in cuerpo
    assert "detail" not in cuerpo


def test_ac02b_texto_que_no_es_una_cadena_devuelve_422_parametros_invalidos(
    cliente: TestClient,
) -> None:
    respuesta = cliente.post("/api/v1/frases/validar", json={"texto": 12345})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "PARAMETROS_INVALIDOS"
    assert "detail" not in cuerpo


def test_ac02b_json_invalido_devuelve_422_parametros_invalidos_con_forma_uniforme(
    cliente: TestClient,
) -> None:
    respuesta = cliente.post(
        "/api/v1/frases/validar",
        content=b"{esto no es json valido",
        headers={"content-type": "application/json"},
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "PARAMETROS_INVALIDOS"
    assert "mensaje" in cuerpo
    assert "detail" not in cuerpo


# FastAPI solo traduce a 422 el `JSONDecodeError`; cualquier otro fallo al leer
# el cuerpo lo envuelve en un `HTTPException(400)`. Estos cuerpos tampoco son
# JSON UTF-8 válido (plan §1) y deben responder igual que uno mal formado.
_CUERPOS_ILEGIBLES = {
    "no_utf8": '{"texto":"rechazó"}'.encode("latin-1"),
    "anidado_sin_limite": b"[" * 100_000 + b"]" * 100_000,
}


@pytest.mark.parametrize("ruta", ["/api/v1/frases/validar", "/api/v1/frases"])
@pytest.mark.parametrize("cuerpo_ilegible", _CUERPOS_ILEGIBLES.values(), ids=_CUERPOS_ILEGIBLES)
def test_ac02b_cuerpo_ilegible_responde_igual_que_un_json_invalido_con_el_campo_cuerpo(
    cliente: TestClient,
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    ruta: str,
    cuerpo_ilegible: bytes,
) -> None:
    repositorio.fallo = RuntimeError("la base no debería consultarse con un cuerpo ilegible")
    cabeceras = {"content-type": "application/json"}
    referencia = cliente.post(ruta, content=b"{esto no es json valido", headers=cabeceras)

    respuesta = cliente.post(ruta, content=cuerpo_ilegible, headers=cabeceras)

    assert respuesta.status_code == 422
    assert respuesta.json() == referencia.json()
    assert respuesta.json() == {
        "codigo": "PARAMETROS_INVALIDOS",
        "mensaje": "La petición no tiene el formato esperado.",
        "detalles": {"cuerpo": "El cuerpo no es JSON válido."},
    }
    assert embedder.textos_recibidos == []


@pytest.mark.parametrize("valor_no_booleano", ["si", "true", 1])
def test_ac02b_confirmar_duplicado_no_booleano_al_guardar_devuelve_422(
    cliente: TestClient, valor_no_booleano: Any
) -> None:
    respuesta = cliente.post(
        "/api/v1/frases",
        json={
            "texto": "Una frase perfectamente válida",
            "confirmar_duplicado": valor_no_booleano,
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "PARAMETROS_INVALIDOS"


def test_ac02b_campos_desconocidos_al_validar_se_ignoran_y_responde_200(
    cliente: TestClient,
) -> None:
    # `confirmar_duplicado` no forma parte del cuerpo de /validar (§1.1): debe
    # ignorarse en lugar de rechazarse.
    respuesta = cliente.post(
        "/api/v1/frases/validar",
        json={"texto": "Una frase perfectamente válida", "confirmar_duplicado": True},
    )

    assert respuesta.status_code == 200


def test_ac02b_texto_de_2001_caracteres_crudos_supera_el_tope_defensivo_y_devuelve_422(
    cliente: TestClient,
) -> None:
    respuesta = cliente.post("/api/v1/frases/validar", json={"texto": "a" * 2001})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "PARAMETROS_INVALIDOS"
