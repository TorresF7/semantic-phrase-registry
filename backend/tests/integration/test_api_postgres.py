"""Flujo completo por HTTP contra PostgreSQL real (AC-07, AC-09, AC-10, AC-11, AC-15, AC-19).

Los tests de `tests/api/` sustituyen el repositorio por uno en memoria, y los
de `test_repositorio_postgres.py` no pasan por HTTP. Estos cierran el hueco:
`TestClient` con `RepositorioPostgres` contra `banco_frases_test`, de modo que
el SQL de pgvector, el desempate y la revalidación al guardar se ejercitan
tal como en producción. Solo el embedder es falso, para fijar el puntaje y no
cargar el modelo.

Requieren la base de test en marcha (`conftest.py` de este paquete), que
además vacía la tabla antes de cada test.
"""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import Configuracion, obtener_configuracion
from app.main import app
from tests.dobles.embedder_falso import FakeEmbedder

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.adapters.persistence.repositorio import RepositorioPostgres

pytestmark = pytest.mark.integration

UMBRAL = 0.75
EXISTENTE = "La entidad bancaria rechazó la transacción"
NUEVA = "El pago fue rechazado por el banco"
PUNTAJE = 0.87


@pytest.fixture
def embedder() -> FakeEmbedder:
    embedder = FakeEmbedder()
    embedder.fijar_similitud(EXISTENTE, NUEVA, PUNTAJE)
    return embedder


@pytest.fixture
def cliente(
    repositorio: "RepositorioPostgres",
    embedder: FakeEmbedder,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    from app.adapters.api.dependencias import obtener_embedder, obtener_repositorio

    configuracion = Configuracion(
        _env_file=None, SIMILARITY_THRESHOLD=UMBRAL, MAX_PHRASE_LENGTH=280
    )
    monkeypatch.setattr(app.state, "fabrica_embedder", lambda nombre_modelo: FakeEmbedder())
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_embedder] = lambda: embedder
    app.dependency_overrides[obtener_configuracion] = lambda: configuracion

    with TestClient(app, raise_server_exceptions=False) as cliente_de_prueba:
        yield cliente_de_prueba

    app.dependency_overrides.clear()
    app.state.embedder = None


def _guardar(cliente: TestClient, texto: str, confirmar: bool = False) -> Any:
    return cliente.post("/api/v1/frases", json={"texto": texto, "confirmar_duplicado": confirmar})


def test_ac07_ac09_ac10_validar_y_guardar_unica_y_la_parecida_sin_confirmar_da_409(
    cliente: TestClient, sesion_sql: "Session"
) -> None:
    validacion = cliente.post("/api/v1/frases/validar", json={"texto": EXISTENTE})
    assert validacion.status_code == 200
    assert validacion.json()["es_posible_duplicado"] is False
    assert validacion.json()["puntaje"] is None  # base vacía (AC-07)

    guardada = _guardar(cliente, EXISTENTE)
    assert guardada.status_code == 201
    assert guardada.json()["estado"] == "UNICA"

    conflicto = _guardar(cliente, NUEVA)
    assert conflicto.status_code == 409
    detalles = conflicto.json()["detalles"]
    assert detalles["motivo"] == "SEMANTICO"
    assert detalles["puntaje"] == pytest.approx(PUNTAJE, abs=1e-6)
    assert detalles["umbral_aplicado"] == UMBRAL
    assert detalles["mas_parecida"] == {"id": guardada.json()["id"], "texto": EXISTENTE}
    # El 409 no escribe nada (RN-12).
    assert sesion_sql.scalar(text("SELECT count(*) FROM frases")) == 1


def test_ac11_ac15_ac19_confirmar_guarda_duplicado_y_el_listado_lo_muestra_con_su_parecida(
    cliente: TestClient, sesion_sql: "Session"
) -> None:
    primera = _guardar(cliente, EXISTENTE).json()
    assert _guardar(cliente, NUEVA).status_code == 409

    confirmada = _guardar(cliente, NUEVA, confirmar=True)

    assert confirmada.status_code == 201
    cuerpo = confirmada.json()
    assert cuerpo["estado"] == "DUPLICADO_CONFIRMADO"
    assert cuerpo["id_mas_parecida"] == primera["id"]
    assert cuerpo["puntaje_similitud"] == pytest.approx(PUNTAJE, abs=1e-6)
    assert cuerpo["umbral_aplicado"] == UMBRAL

    listado = cliente.get("/api/v1/frases", params={"limite": 20, "desplazamiento": 0})
    assert listado.status_code == 200
    pagina = listado.json()
    assert pagina["total"] == 2
    assert [item["texto"] for item in pagina["items"]] == [NUEVA, EXISTENTE]
    assert pagina["items"][0]["mas_parecida"] == {"id": primera["id"], "texto": EXISTENTE}
    assert pagina["items"][1]["mas_parecida"] is None
    # Las dos frases guardan su embedding (RN-14).
    assert sesion_sql.scalar(text("SELECT count(*) FROM frases WHERE embedding IS NULL")) == 0
