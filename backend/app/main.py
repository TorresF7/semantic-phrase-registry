"""Raíz de composición: el único módulo que importa adaptadores concretos."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.api.errores import registrar_manejadores
from app.adapters.api.routers import frases, salud
from app.adapters.embeddings.huggingface import HuggingFaceEmbedder
from app.adapters.persistence.repositorio import RepositorioPostgres
from app.adapters.persistence.sesion import crear_fabrica_sesiones
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
    # El motor no conecta hasta la primera consulta: una base caída no impide
    # arrancar; cada petición que la necesite responde 503 (AC-18).
    app.state.repositorio = RepositorioPostgres(
        crear_fabrica_sesiones(configuracion.url_base_datos)
    )
    yield


# nginx solo reenvía `/api/`: la documentación vive bajo `/api/v1` para verse
# también en Compose. ReDoc no hace falta y no hay OAuth que redirigir.
app = FastAPI(
    title="Banco de Frases",
    lifespan=ciclo_de_vida,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)
# Sustituible: los tests la reemplazan antes de crear el TestClient para no
# cargar el modelo real (plan §7).
app.state.fabrica_embedder = HuggingFaceEmbedder
# Solo hace falta en desarrollo sin Docker: en Compose todo va por nginx (plan §9).
app.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_configuracion().origenes_cors,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
registrar_manejadores(app)
app.include_router(salud.router, prefix="/api/v1")
app.include_router(frases.router, prefix="/api/v1")
