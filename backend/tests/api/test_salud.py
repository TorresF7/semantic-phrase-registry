"""Tests de T-12b: salud y degradación controlada por HTTP (AC-18).

Nivel `tests/api/` (plan §7). `GET /salud` hoy es la versión provisional de
T-02 (`{"estado": "ok", "modelo_cargado": False, "base_datos": "sin
verificar"}`, siempre `200`): estos tests fallan porque ese cuerpo no
distingue el estado real del modelo ni de la base, no por un `ImportError`.

`/salud` es un informe de estado, no un error: no usa la forma uniforme de
AC-14 (`codigo`/`mensaje`/`detalles`), así que estos tests comprueban sus
claves propias (spec AC-18, plan §1.4).
"""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.domain.errores import ErrorRepositorio
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria

# --------------------------------------------------------------------------
# AC-18 (a) — el modelo no pudo cargarse al arrancar (B-09)
# --------------------------------------------------------------------------


def test_ac18_salud_con_modelo_sin_cargar_devuelve_503_degradado(
    cliente_con_arranque_degradado: TestClient,
) -> None:
    respuesta = cliente_con_arranque_degradado.get("/api/v1/salud")

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "degradado"
    assert cuerpo["modelo_cargado"] is False


def test_ac18_validar_frase_nueva_con_modelo_sin_cargar_devuelve_503_servicio_ia_no_disponible(
    cliente_con_arranque_degradado: TestClient,
) -> None:
    respuesta = cliente_con_arranque_degradado.post(
        "/api/v1/frases/validar", json={"texto": "Una frase nueva sin duplicado exacto"}
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "SERVICIO_IA_NO_DISPONIBLE"


def test_ac18_guardar_frase_nueva_con_modelo_sin_cargar_devuelve_503_servicio_ia_no_disponible(
    cliente_con_arranque_degradado: TestClient,
) -> None:
    respuesta = cliente_con_arranque_degradado.post(
        "/api/v1/frases",
        json={"texto": "Otra frase nueva sin duplicado exacto", "confirmar_duplicado": False},
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "SERVICIO_IA_NO_DISPONIBLE"


def test_ac18_listado_con_modelo_sin_cargar_sigue_respondiendo_200(
    cliente_con_arranque_degradado: TestClient,
) -> None:
    # El listado no necesita al proveedor de embeddings.
    respuesta = cliente_con_arranque_degradado.get("/api/v1/frases")

    assert respuesta.status_code == 200


# --------------------------------------------------------------------------
# AC-18 (b) — modelo cargado y base disponible
# --------------------------------------------------------------------------


def test_ac18_salud_con_modelo_cargado_y_base_disponible_devuelve_200_ok(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/v1/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "modelo_cargado": True, "base_datos": "ok"}


# --------------------------------------------------------------------------
# AC-18 (c) — base de datos caída (B-21)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hacer_peticion",
    [
        lambda cliente: cliente.post(
            "/api/v1/frases/validar", json={"texto": "Una frase cualquiera para validar"}
        ),
        lambda cliente: cliente.post(
            "/api/v1/frases",
            json={"texto": "Una frase cualquiera para guardar", "confirmar_duplicado": False},
        ),
        lambda cliente: cliente.get("/api/v1/frases"),
    ],
    ids=["validar", "guardar", "listar"],
)
def test_ac18_base_de_datos_caida_devuelve_503_base_datos_no_disponible(
    cliente: TestClient,
    repositorio: RepositorioEnMemoria,
    hacer_peticion: Callable[[TestClient], Response],
) -> None:
    repositorio.fallo = ErrorRepositorio("no hay conexión con la base de datos")

    respuesta = hacer_peticion(cliente)

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "BASE_DATOS_NO_DISPONIBLE"


def test_ac18_salud_con_base_de_datos_caida_devuelve_503_no_disponible_con_modelo_cargado(
    cliente: TestClient, repositorio: RepositorioEnMemoria
) -> None:
    repositorio.fallo = ErrorRepositorio("no hay conexión con la base de datos")

    respuesta = cliente.get("/api/v1/salud")

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "degradado"
    assert cuerpo["modelo_cargado"] is True
    assert cuerpo["base_datos"] == "no_disponible"
