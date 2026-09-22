"""Fixtures compartidas de `tests/api/` (T-12a, plan §7).

`app.adapters.api.dependencias` todavía no existe: se importa **dentro** de
las fixtures, nunca a nivel de módulo, para que pytest pueda recolectar este
archivo y todos los que lo usan sin un `ImportError` en tiempo de colección.
El error aparece al preparar cada test que necesita el cliente HTTP, que es
donde corresponde mientras la tarea está en rojo.

`app.state.fabrica_embedder` se sustituye **antes** de crear el `TestClient`
(el `lifespan` la llama), como en `tests/api/test_arranque.py`. El repositorio,
el embedder y la configuración se sustituyen con `app.dependency_overrides`
para que ningún test dependa de PostgreSQL real ni del modelo real (plan §7).

`TestClient(app, raise_server_exceptions=False)`: sin este parámetro, un `500`
no manejado se re-lanza en el proceso de test en lugar de devolverse como
respuesta, y AC-14 no podría comprobar su cuerpo (plan §1.5).
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion, obtener_configuracion
from app.main import app
from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


@pytest.fixture
def embedder() -> FakeEmbedder:
    """Embedder falso de la petición bajo prueba, sustituido vía `dependency_overrides`."""
    return FakeEmbedder()


@pytest.fixture
def repositorio() -> RepositorioEnMemoria:
    """Repositorio en memoria de la petición bajo prueba."""
    return RepositorioEnMemoria()


@pytest.fixture
def configuracion_prueba() -> Configuracion:
    """Umbral y longitud máxima explícitos: ningún test depende del valor por defecto (D-07)."""
    return Configuracion(_env_file=None, SIMILARITY_THRESHOLD=0.80, MAX_PHRASE_LENGTH=280)


@pytest.fixture
def cliente(
    embedder: FakeEmbedder,
    repositorio: RepositorioEnMemoria,
    configuracion_prueba: Configuracion,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """`TestClient` con repositorio, embedder y configuración sustituidos.

    Es el cliente por defecto de la suite: usa `obtener_embedder`, así que el
    embedder es siempre el doble inyectado, sin importar el estado de
    `app.state.embedder`. Para el caso en que la propia dependencia debe leer
    `app.state.embedder` (AC-13, sin sustituir `obtener_embedder`), usa
    `cliente_con_arranque_degradado`.
    """
    from app.adapters.api.dependencias import obtener_embedder, obtener_repositorio

    monkeypatch.setattr(app.state, "fabrica_embedder", lambda nombre_modelo: FakeEmbedder())
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_embedder] = lambda: embedder
    app.dependency_overrides[obtener_configuracion] = lambda: configuracion_prueba

    with TestClient(app, raise_server_exceptions=False) as cliente_de_prueba:
        yield cliente_de_prueba

    app.dependency_overrides.clear()
    app.state.embedder = None


@pytest.fixture
def cliente_con_arranque_degradado(
    repositorio: RepositorioEnMemoria,
    configuracion_prueba: Configuracion,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Cliente cuya fábrica de embedder falla al arrancar, dejando `app.state.embedder` en `None`.

    A propósito **no** sustituye `obtener_embedder`: así se comprueba que es
    la propia dependencia la que lee `request.app.state.embedder` y lanza
    `ErrorProveedorEmbeddings` cuando vale `None` (B-09, AC-13), sin que un
    doble de prueba se interponga en el camino.
    """
    from app.adapters.api.dependencias import obtener_repositorio
    from app.domain.errores import ErrorProveedorEmbeddings

    def _fabrica_que_falla(nombre_modelo: str) -> FakeEmbedder:
        raise ErrorProveedorEmbeddings("el modelo no pudo cargarse")

    monkeypatch.setattr(app.state, "fabrica_embedder", _fabrica_que_falla)
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_configuracion] = lambda: configuracion_prueba

    with TestClient(app, raise_server_exceptions=False) as cliente_de_prueba:
        yield cliente_de_prueba

    app.dependency_overrides.clear()
    app.state.embedder = None
