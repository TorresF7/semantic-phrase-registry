"""Endpoints de validación, guardado y listado de frases (plan §1.1 a §1.3)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.adapters.api import documentacion
from app.adapters.api.dependencias import (
    obtener_guardar_frase,
    obtener_repositorio,
    obtener_validar_frase,
)
from app.adapters.api.schemas import (
    FraseRespuesta,
    ItemListado,
    PaginaFrases,
    ResultadoValidacionRespuesta,
    SolicitudGuardado,
    SolicitudValidacion,
)
from app.application.guardar_frase import GuardarFrase
from app.application.validar_frase import ValidarFrase
from app.ports.repositorio import RepositorioFrases

router = APIRouter(prefix="/frases", tags=["frases"])

# Paginación por desplazamiento (RN-17, NF-05).
_LIMITE_POR_DEFECTO = 20
_LIMITE_MAXIMO = 100
# OFFSET es BIGINT en PostgreSQL: por encima, la base rechaza la consulta y se
# respondería 503 como si estuviera caída, cuando es un parámetro inválido.
_DESPLAZAMIENTO_MAXIMO = 2**63 - 1


@router.post(
    "/validar",
    response_model=ResultadoValidacionRespuesta,
    status_code=status.HTTP_200_OK,
    responses={
        200: documentacion.exito(documentacion.EJEMPLO_VALIDACION),
        **documentacion.errores(
            "FRASE_INVALIDA",
            "PARAMETROS_INVALIDOS",
            "ERROR_INTERNO",
            "SERVICIO_IA_NO_DISPONIBLE",
            "BASE_DATOS_NO_DISPONIBLE",
        ),
    },
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
        201: documentacion.exito(documentacion.EJEMPLO_FRASE),
        **documentacion.errores(
            "POSIBLE_DUPLICADO",
            "FRASE_INVALIDA",
            "PARAMETROS_INVALIDOS",
            "ERROR_INTERNO",
            "SERVICIO_IA_NO_DISPONIBLE",
            "BASE_DATOS_NO_DISPONIBLE",
        ),
    },
)
def guardar_frase(
    solicitud: SolicitudGuardado,
    caso_de_uso: Annotated[GuardarFrase, Depends(obtener_guardar_frase)],
) -> FraseRespuesta:
    """Revalida desde cero y guarda si corresponde (RN-11, RN-12)."""
    frase = caso_de_uso.guardar(solicitud.texto, solicitud.confirmar_duplicado)
    return FraseRespuesta.desde_frase(frase)


@router.get(
    "",
    response_model=PaginaFrases,
    status_code=status.HTTP_200_OK,
    responses={
        200: documentacion.exito(documentacion.EJEMPLO_PAGINA),
        **documentacion.errores(
            "PARAMETROS_INVALIDOS",
            "ERROR_INTERNO",
            "BASE_DATOS_NO_DISPONIBLE",
            detalles_parametros={"limite": "Valor no válido."},
        ),
    },
)
def listar_frases(
    repositorio: Annotated[RepositorioFrases, Depends(obtener_repositorio)],
    limite: Annotated[int, Query(ge=1, le=_LIMITE_MAXIMO)] = _LIMITE_POR_DEFECTO,
    desplazamiento: Annotated[int, Query(ge=0, le=_DESPLAZAMIENTO_MAXIMO)] = 0,
) -> PaginaFrases:
    """Frases por fecha de creación descendente, paginadas (RN-17). No necesita el modelo."""
    frases, total = repositorio.listar(limite, desplazamiento)
    return PaginaFrases(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        items=[ItemListado.desde_frase(frase) for frase in frases],
    )
