"""Raíz de composición: el único módulo que importa adaptadores concretos."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.api.routers import salud
from app.adapters.embeddings.huggingface import HuggingFaceEmbedder
from app.config import obtener_configuracion
from app.domain.errores import ErrorProveedorEmbeddings

registro = logging.getLogger(__name__)


# Única función `async` del proyecto: FastAPI solo admite un `lifespan`
# asíncrono. No hay `await` dentro y corre antes de atender peticiones, así que
# cargar el modelo aquí no bloquea a nadie (D-10).
@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Carga el modelo una sola vez por proceso (NF-03).

    Si no carga, el proceso arranca degradado con `embedder = None` (B-09). Si
    carga con una dimensión distinta de la configurada, el arranque falla (B-14).
    """
    configuracion = obtener_configuracion()
    try:
        embedder = app.state.fabrica_embedder(configuracion.nombre_modelo)
    except ErrorProveedorEmbeddings:
        registro.exception("El modelo de embeddings no cargó: se arranca en modo degradado.")
        embedder = None
    if embedder is not None and embedder.dimension != configuracion.dimension_embedding:
        raise RuntimeError(
            f"El modelo {configuracion.nombre_modelo} genera vectores de dimensión "
            f"{embedder.dimension}, pero EMBEDDING_DIMENSION vale "
            f"{configuracion.dimension_embedding}."
        )
    app.state.embedder = embedder
    yield


app = FastAPI(title="Banco de Frases", lifespan=ciclo_de_vida)
# Sustituible: los tests la reemplazan antes de crear el TestClient para no
# cargar el modelo real (plan §7).
app.state.fabrica_embedder = HuggingFaceEmbedder
app.include_router(salud.router, prefix="/api/v1")
