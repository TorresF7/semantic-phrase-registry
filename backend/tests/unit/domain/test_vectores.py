"""Tests de T-05 (Dominio: normalización de vectores y jerarquía de errores).

Cubre RN-19 mediante `normalizar_vector`. El caso de uso completo (con el
embedder falso devolviendo un vector de norma 5) se prueba en T-07 como
AC-17; aquí se prueba la función pura en aislamiento.
"""

import math

import pytest

from app.domain.errores import (
    ErrorDominio,
    ErrorInfraestructura,
    ErrorProveedorEmbeddings,
    ErrorRepositorio,
    FraseInvalida,
    PosibleDuplicado,
)
from app.domain.vectores import normalizar_vector


def test_vector_sin_normalizar_queda_con_norma_uno() -> None:
    resultado = normalizar_vector([3.0, 4.0])

    assert resultado == pytest.approx([0.6, 0.8])


def test_vector_de_384_dimensiones_con_norma_cinco_queda_con_norma_uno() -> None:
    vector = [5.0] + [0.0] * 383

    resultado = normalizar_vector(vector)
    norma = math.sqrt(sum(componente**2 for componente in resultado))

    assert norma == pytest.approx(1.0, abs=1e-6)


def test_la_direccion_del_vector_se_conserva_proporcional() -> None:
    original = [1.0, 2.0, 3.0]

    resultado = normalizar_vector(original)

    factor = resultado[0] / original[0]
    assert resultado == pytest.approx([componente * factor for componente in original])


def test_normalizar_vector_no_muta_la_lista_de_entrada() -> None:
    original = [3.0, 4.0]
    copia = list(original)

    normalizar_vector(original)

    assert original == copia


def test_vector_de_norma_cero_lanza_error_proveedor_embeddings() -> None:
    with pytest.raises(ErrorProveedorEmbeddings):
        normalizar_vector([0.0] * 384)


def test_vector_vacio_lanza_error_proveedor_embeddings() -> None:
    with pytest.raises(ErrorProveedorEmbeddings):
        normalizar_vector([])


def test_jerarquia_de_errores_de_infraestructura_y_de_dominio() -> None:
    assert issubclass(ErrorProveedorEmbeddings, ErrorInfraestructura)
    assert issubclass(ErrorRepositorio, ErrorInfraestructura)
    assert issubclass(FraseInvalida, ErrorDominio)
    assert issubclass(PosibleDuplicado, ErrorDominio)
