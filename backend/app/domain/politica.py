"""Política de umbral y recorte del puntaje (RN-05, RN-06)."""


def es_posible_duplicado(puntaje: float | None, umbral: float) -> bool:
    """Comparación `>=` sobre el puntaje sin redondear (B-08, B-16).

    Un puntaje nulo significa que no hubo con qué comparar (RN-09).
    """
    return puntaje is not None and puntaje >= umbral


def recortar_puntaje(puntaje: float) -> float:
    """Lleva el coseno, que vive en [-1, 1], al rango [0, 1] (B-15)."""
    return min(max(puntaje, 0.0), 1.0)
