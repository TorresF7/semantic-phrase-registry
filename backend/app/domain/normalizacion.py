"""Normalización y validación del texto de una frase (RN-01, RN-02, RN-03)."""

import unicodedata

from app.domain.errores import FraseInvalida

LONGITUD_MINIMA = 3


def normalizar(texto: str) -> str:
    """NFKC, sin caracteres de formato, recorte, colapso de espacios y minúsculas (RN-02).

    Los caracteres de formato (categoría Unicode Cf: U+200B, U+FEFF, U+00AD…)
    no se ven y llegan sin querer al copiar: se eliminan antes de colapsar, para
    que uno junto a un espacio no deje dos (B-28, D-41). `str.split()` sin
    argumentos separa por cualquier espacio Unicode, así que recorta y colapsa
    tabulaciones, saltos de línea y espacios duros en un paso (B-17).
    """
    compatible = unicodedata.normalize("NFKC", texto)
    sin_formato = "".join(c for c in compatible if unicodedata.category(c) != "Cf")
    return " ".join(sin_formato.split()).lower()


def normalizar_y_validar(texto: str, longitud_maxima: int) -> str:
    """Devuelve el texto normalizado si es texto plano y su longitud está en rango.

    RN-01 y RN-03. La longitud se mide sobre el texto normalizado, en puntos de
    código. Los caracteres de control que son espacio ya se colapsaron al
    normalizar; cualquier otro (categoría Unicode Cc, como U+0000) se rechaza
    (B-27).
    """
    normalizado = normalizar(texto)
    if any(unicodedata.category(caracter) == "Cc" for caracter in normalizado):
        raise FraseInvalida("La frase contiene caracteres no permitidos.")
    if len(normalizado) < LONGITUD_MINIMA:
        raise FraseInvalida(f"La frase debe tener al menos {LONGITUD_MINIMA} caracteres.")
    if len(normalizado) > longitud_maxima:
        raise FraseInvalida(f"La frase no puede tener más de {longitud_maxima} caracteres.")
    return normalizado
