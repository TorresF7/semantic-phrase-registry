"""Tests de T-10 (Adaptador de Hugging Face).

Nivel `tests/unit/adapters/`: rápidos, sin `torch` ni `sentence-transformers`
instalados de verdad. El módulo `sentence_transformers` se simula con
`monkeypatch.setitem(sys.modules, ...)`, aprovechando que el import de
`HuggingFaceEmbedder` es perezoso, dentro de su constructor (plan §3, skill
python-backend).

`HuggingFaceEmbedder` todavía no existe (T-10 sin implementar). El import se
hace dentro de una función auxiliar, no a nivel de módulo, para que cada test
falle de forma independiente con `ModuleNotFoundError` sin romper la
recolección del resto de la suite.

El test con el modelo real vive en `tests/unit/adapters/test_modelo_real.py`,
marcado `slow` (plan §7).
"""

import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from app.domain.errores import ErrorProveedorEmbeddings


def _clase_huggingface_embedder() -> type:
    from app.adapters.embeddings.huggingface import HuggingFaceEmbedder

    return HuggingFaceEmbedder


def _instalar_sentence_transformers_falso(
    monkeypatch: pytest.MonkeyPatch, clase_modelo: type
) -> None:
    modulo_falso = types.ModuleType("sentence_transformers")
    modulo_falso.SentenceTransformer = clase_modelo  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", modulo_falso)


def test_fallo_de_encode_se_traduce_a_error_proveedor_embeddings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ModeloQueFallaAlCodificar:
        def __init__(self, nombre_modelo: str) -> None:
            self._nombre_modelo = nombre_modelo

        def get_embedding_dimension(self) -> int:
            return 384

        def encode(self, texto: str, normalize_embeddings: bool = True) -> Any:
            raise RuntimeError("el modelo no pudo procesar el texto")

    _instalar_sentence_transformers_falso(monkeypatch, ModeloQueFallaAlCodificar)
    clase_huggingface_embedder = _clase_huggingface_embedder()
    embedder = clase_huggingface_embedder("modelo-de-prueba")

    with pytest.raises(ErrorProveedorEmbeddings) as info:
        embedder.generar("una frase cualquiera")

    assert isinstance(info.value.__cause__, RuntimeError)


def test_fallo_al_cargar_el_modelo_se_traduce_a_error_proveedor_embeddings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ModeloQueNoSeDescarga:
        def __init__(self, nombre_modelo: str) -> None:
            raise OSError("no se pudo descargar el modelo")

    _instalar_sentence_transformers_falso(monkeypatch, ModeloQueNoSeDescarga)
    clase_huggingface_embedder = _clase_huggingface_embedder()

    with pytest.raises(ErrorProveedorEmbeddings) as info:
        clase_huggingface_embedder("modelo-inexistente")

    assert isinstance(info.value.__cause__, OSError)


def test_generar_pasa_el_texto_y_normalize_embeddings_true_y_devuelve_lista_de_floats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[tuple[str, bool]] = []

    class VectorConTolist:
        def tolist(self) -> list[float]:
            return [0.1, 0.2, 0.3]

    class ModeloQueRegistraLaLlamada:
        def __init__(self, nombre_modelo: str) -> None:
            pass

        def get_embedding_dimension(self) -> int:
            return 384

        def encode(self, texto: str, normalize_embeddings: bool = True) -> Any:
            llamadas.append((texto, normalize_embeddings))
            return VectorConTolist()

    _instalar_sentence_transformers_falso(monkeypatch, ModeloQueRegistraLaLlamada)
    clase_huggingface_embedder = _clase_huggingface_embedder()
    embedder = clase_huggingface_embedder("modelo-de-prueba")

    vector = embedder.generar("el pago fue rechazado")

    assert llamadas == [("el pago fue rechazado", True)]
    assert vector == [0.1, 0.2, 0.3]
    assert isinstance(vector, list)
    assert all(isinstance(componente, float) for componente in vector)


def test_generar_acepta_una_tupla_de_encode_y_la_convierte_a_lista_de_floats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ModeloQueDevuelveUnaTupla:
        def __init__(self, nombre_modelo: str) -> None:
            pass

        def get_embedding_dimension(self) -> int:
            return 3

        def encode(self, texto: str, normalize_embeddings: bool = True) -> Any:
            return (0.5, -0.5, 0.7)

    _instalar_sentence_transformers_falso(monkeypatch, ModeloQueDevuelveUnaTupla)
    clase_huggingface_embedder = _clase_huggingface_embedder()
    embedder = clase_huggingface_embedder("modelo-de-prueba")

    vector = embedder.generar("otra frase")

    assert vector == [0.5, -0.5, 0.7]
    assert isinstance(vector, list)


def test_nombre_modelo_y_dimension_reflejan_el_modelo_cargado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ModeloDeDimensionFija:
        def __init__(self, nombre_modelo: str) -> None:
            pass

        def get_embedding_dimension(self) -> int:
            return 512

    _instalar_sentence_transformers_falso(monkeypatch, ModeloDeDimensionFija)
    clase_huggingface_embedder = _clase_huggingface_embedder()

    embedder = clase_huggingface_embedder("sentence-transformers/otro-modelo")

    assert embedder.nombre_modelo == "sentence-transformers/otro-modelo"
    assert embedder.dimension == 512


def test_importar_app_main_no_carga_torch_y_expone_la_fabrica_de_embedder() -> None:
    """DoD de T-10: la suite rápida corre sin `torch` importado (plan §7, tasks.md).

    Se comprueba en un subproceso limpio, importando solo `app.main`, sin pasar
    por el `lifespan` (que sí construiría el embedder real si no se sustituye
    la fábrica). También comprueba que `app.state.fabrica_embedder` queda
    expuesta al cargar el módulo, que es lo que hace posible sustituirla en
    `tests/api/test_arranque.py` sin cargar el modelo real.
    """
    directorio_backend = Path(__file__).resolve().parents[3]
    script = (
        "import sys\n"
        "import app.main\n"
        "assert hasattr(app.main.app.state, 'fabrica_embedder'), ("
        "'app.state.fabrica_embedder debe existir tras cargar app.main'"
        ")\n"
        "assert 'torch' not in sys.modules, 'importar app.main no debe cargar torch'\n"
        "assert 'sentence_transformers' not in sys.modules, ("
        "'importar app.main no debe cargar sentence_transformers'"
        ")\n"
        "print('ok')\n"
    )

    resultado = subprocess.run(
        [sys.executable, "-c", script],
        cwd=directorio_backend,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
