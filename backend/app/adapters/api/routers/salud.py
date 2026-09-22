"""Estado del servicio (plan §1.4, AC-18)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.adapters.api import documentacion
from app.adapters.api.dependencias import obtener_repositorio
from app.adapters.api.schemas import EstadoSalud
from app.ports.repositorio import RepositorioFrases

router = APIRouter(tags=["salud"])


@router.get(
    "/salud",
    response_model=EstadoSalud,
    status_code=status.HTTP_200_OK,
    responses=documentacion.RESPUESTAS_SALUD,
)
def consultar_salud(
    request: Request,
    response: Response,
    repositorio: Annotated[RepositorioFrases, Depends(obtener_repositorio)],
) -> EstadoSalud:
    """`200` si el modelo está cargado y la base responde; si no, `503` degradado (B-09, B-21)."""
    modelo_cargado = request.app.state.embedder is not None
    base_disponible = repositorio.esta_disponible()
    if not (modelo_cargado and base_disponible):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return EstadoSalud(
        estado="ok" if modelo_cargado and base_disponible else "degradado",
        modelo_cargado=modelo_cargado,
        base_datos="ok" if base_disponible else "no_disponible",
    )
