"""Funciones para `Depends`: leen los adaptadores de `app.state` y arman los casos de uso.

No importan `persistence` ni `embeddings`: los adaptadores concretos los cablea
`app/main.py` en el `lifespan` (plan §4). Los tests las sustituyen con
`app.dependency_overrides`.
"""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request

from app.application.guardar_frase import GuardarFrase
from app.application.validar_frase import ValidarFrase
from app.config import Configuracion, obtener_configuracion
from app.domain.errores import ErrorProveedorEmbeddings
from app.ports.embeddings import ProveedorEmbeddings
from app.ports.repositorio import RepositorioFrases


def obtener_repositorio(request: Request) -> RepositorioFrases:
    repositorio: RepositorioFrases = request.app.state.repositorio
    return repositorio


class EmbedderNoDisponible:
    """Sustituto del modelo que no cargó al arrancar (B-09, D-21).

    Solo falla cuando de verdad hace falta generar un vector: validar un
    duplicado exacto no lo necesita y responde con normalidad (RN-15, B-20).
    """

    def __init__(self, nombre_modelo: str, dimension: int) -> None:
        self._nombre_modelo = nombre_modelo
        self._dimension = dimension

    @property
    def nombre_modelo(self) -> str:
        return self._nombre_modelo

    @property
    def dimension(self) -> int:
        return self._dimension

    def generar(self, texto: str) -> list[float]:
        raise ErrorProveedorEmbeddings("El modelo de embeddings no está cargado.")


ConfiguracionActual = Annotated[Configuracion, Depends(obtener_configuracion)]


def obtener_embedder(request: Request, configuracion: ConfiguracionActual) -> ProveedorEmbeddings:
    embedder: ProveedorEmbeddings | None = request.app.state.embedder
    if embedder is None:
        return EmbedderNoDisponible(configuracion.nombre_modelo, configuracion.dimension_embedding)
    return embedder


Repositorio = Annotated[RepositorioFrases, Depends(obtener_repositorio)]
Embedder = Annotated[ProveedorEmbeddings, Depends(obtener_embedder)]


def obtener_validar_frase(
    repositorio: Repositorio, embedder: Embedder, configuracion: ConfiguracionActual
) -> ValidarFrase:
    return ValidarFrase(
        repositorio,
        embedder,
        umbral=configuracion.umbral_similitud,
        longitud_maxima=configuracion.longitud_maxima_frase,
    )


def obtener_guardar_frase(
    repositorio: Repositorio, embedder: Embedder, configuracion: ConfiguracionActual
) -> GuardarFrase:
    return GuardarFrase(
        repositorio,
        embedder,
        umbral=configuracion.umbral_similitud,
        longitud_maxima=configuracion.longitud_maxima_frase,
    )


if TYPE_CHECKING:
    # mypy comprueba aquí que el sustituto implementa el puerto.
    _conforme: ProveedorEmbeddings = EmbedderNoDisponible("", 0)
