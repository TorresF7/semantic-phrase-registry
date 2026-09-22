"""Normalización de embeddings (RN-19)."""

import math

from app.domain.errores import ErrorProveedorEmbeddings


def normalizar_vector(vector: list[float]) -> list[float]:
    """Devuelve un vector nuevo con la misma dirección y norma 1.

    Un vector de norma cero no tiene dirección: se trata como fallo del
    proveedor (RN-15).
    """
    norma = math.sqrt(sum(componente * componente for componente in vector))
    if norma == 0.0:
        raise ErrorProveedorEmbeddings("El proveedor devolvió un vector de norma cero.")
    return [componente / norma for componente in vector]
