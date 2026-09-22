"""Tests de T-10 (Arranque degradado y comprobación de dimensión, B-09 y B-14).

Nivel `tests/api/`: usan `TestClient` para ejercitar el `lifespan` de
`app.main`, sustituyendo `app.state.fabrica_embedder` **antes** de crear el
cliente, como exige el plan §7. Ningún test de este archivo carga el modelo
real ni depende de `torch`: la fábrica siempre se sustituye por una que
devuelve (o falla al construir) un `FakeEmbedder`.

`app.state.fabrica_embedder` todavía no existe en `app.main` (T-10 sin
implementar): `monkeypatch.setattr` falla con `AttributeError` porque, por
defecto, exige que el atributo exista de antemano. Es el fallo esperado hasta
que T-10 lo cablee en el `lifespan`.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import obtener_configuracion
from app.domain.errores import ErrorProveedorEmbeddings
from app.main import app
from app.ports.embeddings import ProveedorEmbeddings
from tests.dobles.embedder_falso import FakeEmbedder


@pytest.fixture(autouse=True)
def _limpiar_estado_tras_cada_test() -> Iterator[None]:
    """Evita que un test deje el embedder o la configuración cacheada para el siguiente."""
    yield
    app.state.embedder = None
    obtener_configuracion.cache_clear()


def test_b09_fabrica_que_falla_deja_el_arranque_degradado_sin_embedder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fabrica_que_falla(nombre_modelo: str) -> ProveedorEmbeddings:
        raise ErrorProveedorEmbeddings("el modelo no pudo cargarse")

    monkeypatch.setattr(app.state, "fabrica_embedder", _fabrica_que_falla)

    with TestClient(app):
        pass

    assert app.state.embedder is None


def test_fabrica_que_carga_correctamente_deja_el_embedder_devuelto_en_app_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedder_esperado = FakeEmbedder()
    monkeypatch.setattr(app.state, "fabrica_embedder", lambda nombre_modelo: embedder_esperado)

    with TestClient(app):
        assert app.state.embedder is embedder_esperado


def test_b14_dimension_del_embedder_distinta_de_la_configurada_hace_fallar_el_arranque(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Se fija explícitamente en 384, sin depender del .env de quien ejecuta
    # los tests, y se limpia la caché de `Configuracion` para que el nuevo
    # valor de entorno se lea de verdad (D-14, STATUS.md).
    monkeypatch.setenv("EMBEDDING_DIMENSION", "384")
    obtener_configuracion.cache_clear()
    monkeypatch.setattr(
        app.state, "fabrica_embedder", lambda nombre_modelo: FakeEmbedder(dimension=512)
    )

    # B-14: el arranque falla "con un mensaje claro" que nombre la variable.
    with pytest.raises(RuntimeError, match="EMBEDDING_DIMENSION"), TestClient(app):
        pass
