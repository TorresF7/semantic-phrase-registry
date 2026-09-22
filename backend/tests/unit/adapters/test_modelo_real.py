"""Test lento de T-10: `HuggingFaceEmbedder` con el modelo real (plan §7).

Se ubica junto al resto de tests del adaptador (`tests/unit/adapters/`) en
lugar de en un directorio `tests/slow/` nuevo: la tabla de niveles de la skill
`testing` distingue "marcados `slow`" por el marcador de pytest, no por una
carpeta propia, y el proyecto no tiene precedente de una carpeta dedicada solo
a la velocidad. Mantenerlo junto a `test_huggingface.py` evita introducir una
convención de carpetas nueva sin necesidad.

Marcado `slow`: descarga y carga
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (~23 s en frío,
ver `docs/STATUS.md`). No corre en `pytest -m "not slow and not
integration"`. Los umbrales están escritos en este archivo, no salen de
`SIMILARITY_THRESHOLD`: es una comprobación de humo sobre el modelo real, AC-04
y AC-05 ya están cubiertos con `FakeEmbedder` en T-07.

El import de `HuggingFaceEmbedder` se hace dentro del fixture, no a nivel de
módulo (el adaptador todavía no existe, T-10 sin implementar), para que la
recolección de este archivo no rompa por un `ModuleNotFoundError` a nivel de
módulo. `from __future__ import annotations` evita que las anotaciones de tipo
que nombran la clase se evalúen en tiempo de importación.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from app.domain.normalizacion import normalizar

if TYPE_CHECKING:
    from app.adapters.embeddings.huggingface import HuggingFaceEmbedder

pytestmark = pytest.mark.slow

_NOMBRE_MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@pytest.fixture(scope="module")
def embedder() -> HuggingFaceEmbedder:
    from app.adapters.embeddings.huggingface import HuggingFaceEmbedder as Clase

    return Clase(_NOMBRE_MODELO)


def _coseno(vector_a: list[float], vector_b: list[float]) -> float:
    producto_punto = sum(a * b for a, b in zip(vector_a, vector_b, strict=True))
    norma_a = math.sqrt(sum(a * a for a in vector_a))
    norma_b = math.sqrt(sum(b * b for b in vector_b))
    return producto_punto / (norma_a * norma_b)


def test_dos_parafrasis_del_par_estrella_de_t00_superan_0_80(embedder: HuggingFaceEmbedder) -> None:
    vector_a = embedder.generar(normalizar("El pago fue rechazado por el banco"))
    vector_b = embedder.generar(normalizar("La entidad bancaria rechazó la transacción"))

    assert _coseno(vector_a, vector_b) > 0.80


def test_dos_frases_sin_relacion_no_llegan_a_0_50(embedder: HuggingFaceEmbedder) -> None:
    vector_a = embedder.generar(normalizar("El pago fue rechazado por el banco"))
    vector_b = embedder.generar(normalizar("Mañana lloverá en la costa"))

    assert _coseno(vector_a, vector_b) < 0.50


def test_la_dimension_del_modelo_real_es_384(embedder: HuggingFaceEmbedder) -> None:
    assert embedder.dimension == 384


def test_el_vector_generado_tiene_norma_aproximadamente_1(embedder: HuggingFaceEmbedder) -> None:
    vector = embedder.generar(normalizar("Una frase cualquiera para medir la norma"))
    norma = math.sqrt(sum(componente * componente for componente in vector))

    assert norma == pytest.approx(1.0, abs=1e-6)
