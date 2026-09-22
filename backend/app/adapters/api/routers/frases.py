"""Endpoints de validación y guardado de frases (plan §1.1 y §1.2)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.adapters.api.dependencias import obtener_guardar_frase, obtener_validar_frase
from app.adapters.api.schemas import (
    ErrorRespuesta,
    FraseRespuesta,
    ResultadoValidacionRespuesta,
    SolicitudGuardado,
    SolicitudValidacion,
)
from app.application.guardar_frase import GuardarFrase
from app.application.validar_frase import ValidarFrase

router = APIRouter(prefix="/frases", tags=["frases"])

_ERRORES_COMUNES: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorRespuesta, "description": "FRASE_INVALIDA o PARAMETROS_INVALIDOS"},
    503: {
        "model": ErrorRespuesta,
        "description": "SERVICIO_IA_NO_DISPONIBLE o BASE_DATOS_NO_DISPONIBLE",
    },
    500: {"model": ErrorRespuesta, "description": "ERROR_INTERNO"},
}


@router.post(
    "/validar",
    response_model=ResultadoValidacionRespuesta,
    status_code=status.HTTP_200_OK,
    responses=_ERRORES_COMUNES,
)
def validar_frase(
    solicitud: SolicitudValidacion,
    caso_de_uso: Annotated[ValidarFrase, Depends(obtener_validar_frase)],
) -> ResultadoValidacionRespuesta:
    """Compara la frase con las registradas. No guarda nada (RN-10)."""
    return ResultadoValidacionRespuesta.desde_resultado(caso_de_uso.validar(solicitud.texto))


@router.post(
    "",
    response_model=FraseRespuesta,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorRespuesta, "description": "POSIBLE_DUPLICADO sin confirmar"},
        **_ERRORES_COMUNES,
    },
)
def guardar_frase(
    solicitud: SolicitudGuardado,
    caso_de_uso: Annotated[GuardarFrase, Depends(obtener_guardar_frase)],
) -> FraseRespuesta:
    """Revalida desde cero y guarda si corresponde (RN-11, RN-12)."""
    frase = caso_de_uso.guardar(solicitud.texto, solicitud.confirmar_duplicado)
    return FraseRespuesta.desde_frase(frase)
