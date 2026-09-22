"""Normalización y validación del texto de una frase (RN-01, RN-02, RN-03)."""

import unicodedata

from app.domain.errores import FraseInvalida

LONGITUD_MINIMA = 3


def normalizar(texto: str) -> str:
    """NFKC, recorte, colapso de espacios y minúsculas, en ese orden (RN-02).

    `str.split()` sin argumentos separa por cualquier espacio Unicode, así que
    recorta y colapsa tabulaciones, saltos de línea y espacios duros en un paso
    (B-17).
    """
    return " ".join(unicodedata.normalize("NFKC", texto).split()).lower()


def normalizar_y_validar(texto: str, longitud_maxima: int) -> str:
    """Devuelve el texto normalizado si su longitud está en rango (RN-01, RN-03).

    La longitud se mide sobre el texto normalizado, en puntos de código.
    """
    normalizado = normalizar(texto)
    if len(normalizado) < LONGITUD_MINIMA:
        raise FraseInvalida(f"La frase debe tener al menos {LONGITUD_MINIMA} caracteres.")
    if len(normalizado) > longitud_maxima:
        raise FraseInvalida(f"La frase no puede tener más de {longitud_maxima} caracteres.")
    return normalizado
