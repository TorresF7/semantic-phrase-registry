"""Tests de T-12a: estructura uniforme de error por HTTP (AC-14).

`{codigo, mensaje, detalles}` en 404, 405, 409, 422, 500 y 503 — incluidos los
errores que genera el propio framework (ruta inexistente, método no permitido,
cuerpo mal formado), no solo los que lanza el dominio (plan §1.5).
"""

from typing import Any

from fastapi.testclient import TestClient

from app.domain.errores import ErrorRepositorio
from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


def _forma_uniforme(cuerpo: dict[str, Any]) -> bool:
    """`codigo` y `mensaje` presentes; ninguna clave ajena a {codigo, mensaje, detalles}."""
    return (
        "codigo" in cuerpo
        and "mensaje" in cuerpo
        and "detail" not in cuerpo
        and set(cuerpo.keys()) <= {"codigo", "mensaje", "detalles"}
    )


def test_ac14_ruta_inexistente_devuelve_404_no_encontrado_con_forma_uniforme(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/v1/no-existe")

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "NO_ENCONTRADO"
    assert _forma_uniforme(cuerpo)


def test_ac14_metodo_no_permitido_devuelve_405_con_forma_uniforme(cliente: TestClient) -> None:
    # Solo POST está admitido en /frases/validar.
    respuesta = cliente.get("/api/v1/frases/validar")

    assert respuesta.status_code == 405
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "METODO_NO_PERMITIDO"
    assert _forma_uniforme(cuerpo)


def test_ac14_posible_duplicado_devuelve_409_con_forma_uniforme(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    repositorio.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()

    respuesta = cliente.post(
        "/api/v1/frases", json={"texto": texto_nuevo, "confirmar_duplicado": False}
    )

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "POSIBLE_DUPLICADO"
    assert _forma_uniforme(cuerpo)


def test_ac14_cuerpo_mal_formado_devuelve_422_con_forma_uniforme(cliente: TestClient) -> None:
    respuesta = cliente.post("/api/v1/frases/validar", json={})

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "PARAMETROS_INVALIDOS"
    assert _forma_uniforme(cuerpo)


def test_ac14_excepcion_generica_del_repositorio_devuelve_500_error_interno_sin_trazas(
    cliente: TestClient, repositorio: RepositorioEnMemoria
) -> None:
    repositorio.fallo = RuntimeError("secreto-interno")

    respuesta = cliente.post(
        "/api/v1/frases/validar", json={"texto": "Una frase válida cualquiera"}
    )

    assert respuesta.status_code == 500
    cuerpo_texto = respuesta.text
    assert "secreto-interno" not in cuerpo_texto
    assert "RuntimeError" not in cuerpo_texto
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "ERROR_INTERNO"
    assert _forma_uniforme(cuerpo)


def test_ac14_base_de_datos_caida_devuelve_503_base_datos_no_disponible(
    cliente: TestClient, repositorio: RepositorioEnMemoria
) -> None:
    repositorio.fallo = ErrorRepositorio("no hay conexión con la base de datos")

    respuesta = cliente.post(
        "/api/v1/frases/validar", json={"texto": "Otra frase válida cualquiera"}
    )

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "BASE_DATOS_NO_DISPONIBLE"
    assert _forma_uniforme(cuerpo)
