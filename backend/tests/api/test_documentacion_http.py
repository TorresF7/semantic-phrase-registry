"""Documentación interactiva accesible detrás de nginx.

nginx solo reenvía `/api/` al backend (plan §9): Swagger UI y el esquema
OpenAPI tienen que vivir bajo `/api/v1` para verse en `http://localhost:8080`.
ReDoc se desactiva: con Swagger basta. Sin AC propio, se nombran de forma
descriptiva (skill de testing, sección "Nomenclatura").
"""

import pytest
from fastapi.testclient import TestClient


def test_swagger_ui_se_sirve_bajo_api_v1_y_apunta_al_esquema_bajo_api_v1(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/v1/docs")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "/api/v1/openapi.json" in respuesta.text


def test_esquema_openapi_se_sirve_bajo_api_v1(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/openapi.json")

    assert respuesta.status_code == 200
    assert "/api/v1/frases" in respuesta.json()["paths"]


@pytest.mark.parametrize(
    "ruta",
    ["/docs", "/redoc", "/openapi.json", "/api/v1/redoc", "/docs/oauth2-redirect"],
)
def test_rutas_de_documentacion_fuera_de_api_v1_o_de_redoc_no_existen(
    cliente: TestClient, ruta: str
) -> None:
    assert cliente.get(ruta).status_code == 404
