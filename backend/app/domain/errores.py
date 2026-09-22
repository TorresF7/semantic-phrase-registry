"""Jerarquía de errores del sistema.

El dominio y la aplicación lanzan `ErrorDominio`. Los adaptadores traducen los
fallos de sus librerías a `ErrorInfraestructura` en su frontera. Solo la capa
HTTP los convierte en códigos de estado (RN-16).
"""

from app.domain.entidades import ResultadoValidacion


class ErrorDominio(Exception):
    """Una regla de negocio impide completar la operación."""


class FraseInvalida(ErrorDominio):
    """El texto normalizado no cumple RN-01 o RN-03. El mensaje es para la persona."""


class PosibleDuplicado(ErrorDominio):
    """Se intentó guardar un posible duplicado sin confirmarlo (RN-12).

    Lleva el resultado de la revalidación: el 409 lo devuelve como detalle.
    """

    def __init__(self, resultado: ResultadoValidacion) -> None:
        super().__init__("Ya existe una frase muy parecida a la que intentas guardar.")
        self.resultado = resultado


class ErrorInfraestructura(Exception):
    """Un componente externo falló o no está disponible (RN-15)."""


class ErrorProveedorEmbeddings(ErrorInfraestructura):
    """El proveedor de embeddings falló o devolvió un vector inservible."""


class ErrorRepositorio(ErrorInfraestructura):
    """La base de datos falló o no está disponible."""
