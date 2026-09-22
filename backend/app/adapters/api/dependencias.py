"""Funciones para `Depends`: leen los adaptadores de `app.state` y arman los casos de uso.

No importan `persistence` ni `embeddings`: los adaptadores concretos los cablea
`app/main.py` en el `lifespan` (plan §4). Los tests las sustituyen con
`app.dependency_overrides`.
"""

from typing import Annotated

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


def obtener_embedder(request: Request) -> ProveedorEmbeddings:
    embedder: ProveedorEmbeddings | None = request.app.state.embedder
    if embedder is None:
        # El modelo no cargó al arrancar: el proceso sigue en pie, degradado (B-09).
        raise ErrorProveedorEmbeddings("El modelo de embeddings no está cargado.")
    return embedder


Repositorio = Annotated[RepositorioFrases, Depends(obtener_repositorio)]
Embedder = Annotated[ProveedorEmbeddings, Depends(obtener_embedder)]
ConfiguracionActual = Annotated[Configuracion, Depends(obtener_configuracion)]


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
