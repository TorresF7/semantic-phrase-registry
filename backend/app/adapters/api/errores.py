"""Traducción de excepciones a respuestas HTTP con forma uniforme (RN-16, plan §1.5).

Es el único lugar que conoce los códigos de estado. Sustituye también los
manejadores por defecto de FastAPI, que responden `{"detail": ...}` (AC-14).
Ninguna respuesta incluye trazas, nombres de clase ni texto de excepciones
ajenas: los mensajes son fijos, salvo los del dominio, escritos para la persona.
"""

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.api.schemas import ResultadoValidacionRespuesta
from app.domain.errores import (
    ErrorProveedorEmbeddings,
    ErrorRepositorio,
    FraseInvalida,
    PosibleDuplicado,
)

registro = logging.getLogger(__name__)

MENSAJE_PARAMETROS = "La petición no tiene el formato esperado."
MENSAJE_IA = "El servicio que compara frases no está disponible. Inténtalo más tarde."
MENSAJE_BASE_DATOS = "No se puede acceder a las frases guardadas. Inténtalo más tarde."
MENSAJE_INTERNO = "Ocurrió un error inesperado. Inténtalo más tarde."

_ERRORES_HTTP = {
    404: ("NO_ENCONTRADO", "La ruta solicitada no existe."),
    405: ("METODO_NO_PERMITIDO", "Este método no está permitido en la ruta solicitada."),
}

# Mensajes por tipo de error de Pydantic: los suyos están en inglés y nombran
# tipos internos. Lo que no está aquí recibe el mensaje genérico.
_MENSAJES_POR_TIPO = {
    "missing": "Campo obligatorio.",
    "string_type": "Debe ser un texto.",
    "string_too_long": "El texto es demasiado largo.",
    "bool_type": "Debe ser verdadero o falso.",
    "json_invalid": "El cuerpo no es JSON válido.",
    "model_attributes_type": "El cuerpo debe ser un objeto JSON.",
}


def _respuesta(
    estado: int,
    codigo: str,
    mensaje: str,
    detalles: dict[str, Any] | None = None,
    cabeceras: Mapping[str, str] | None = None,
) -> JSONResponse:
    cuerpo: dict[str, Any] = {"codigo": codigo, "mensaje": mensaje}
    if detalles is not None:
        cuerpo["detalles"] = detalles
    return JSONResponse(status_code=estado, content=cuerpo, headers=cabeceras)


def _campo(ubicacion: tuple[int | str, ...]) -> str:
    """`("body", "texto")` → `"texto"`; el cuerpo entero o una posición del JSON → `"cuerpo"`."""
    nombres = [parte for parte in ubicacion[1:] if isinstance(parte, str)]
    return ".".join(nombres) if nombres else "cuerpo"


def _frase_invalida(_: Request, error: Exception) -> JSONResponse:
    mensaje = str(error)
    return _respuesta(422, "FRASE_INVALIDA", mensaje, {"texto": mensaje})


def _parametros_invalidos(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    detalles = {
        _campo(tuple(fallo["loc"])): _MENSAJES_POR_TIPO.get(fallo["type"], "Valor no válido.")
        for fallo in error.errors()
    }
    return _respuesta(422, "PARAMETROS_INVALIDOS", MENSAJE_PARAMETROS, detalles)


def _posible_duplicado(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, PosibleDuplicado)
    resultado = ResultadoValidacionRespuesta.desde_resultado(error.resultado)
    detalles = resultado.model_dump(
        mode="json", include={"puntaje", "umbral_aplicado", "motivo", "mas_parecida"}
    )
    return _respuesta(409, "POSIBLE_DUPLICADO", str(error), detalles)


def _proveedor_no_disponible(_: Request, error: Exception) -> JSONResponse:
    registro.error("Proveedor de embeddings no disponible: %s", error)
    return _respuesta(503, "SERVICIO_IA_NO_DISPONIBLE", MENSAJE_IA)


def _base_datos_no_disponible(_: Request, error: Exception) -> JSONResponse:
    # La causa lleva la consulta SQL: va al log, nunca a la respuesta.
    registro.error("Base de datos no disponible: %r", error.__cause__)
    return _respuesta(503, "BASE_DATOS_NO_DISPONIBLE", MENSAJE_BASE_DATOS)


def _error_http(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, StarletteHTTPException)
    if error.status_code == 400:
        # FastAPI solo traduce a 422 el `JSONDecodeError`; cualquier otro fallo
        # al leer el cuerpo (bytes que no son UTF-8, anidamiento sin límite) lo
        # lanza como 400. Tampoco es JSON UTF-8 válido (plan §1): mismo 422.
        detalles = {"cuerpo": _MENSAJES_POR_TIPO["json_invalid"]}
        return _respuesta(
            422, "PARAMETROS_INVALIDOS", MENSAJE_PARAMETROS, detalles, cabeceras=error.headers
        )
    # Ni la aplicación ni el framework, tal como se usan, lanzan otros estados;
    # si apareciera uno, se conserva el estado pero el cuerpo no promete un
    # código que el catálogo no define.
    codigo, mensaje = _ERRORES_HTTP.get(error.status_code, ("ERROR_INTERNO", MENSAJE_INTERNO))
    # Conserva cabeceras como `Allow` del 405.
    return _respuesta(error.status_code, codigo, mensaje, cabeceras=error.headers)


def _error_interno(_: Request, error: Exception) -> JSONResponse:
    registro.exception("Error no controlado", exc_info=error)
    return _respuesta(500, "ERROR_INTERNO", MENSAJE_INTERNO)


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(FraseInvalida, _frase_invalida)
    app.add_exception_handler(RequestValidationError, _parametros_invalidos)
    app.add_exception_handler(PosibleDuplicado, _posible_duplicado)
    app.add_exception_handler(ErrorProveedorEmbeddings, _proveedor_no_disponible)
    app.add_exception_handler(ErrorRepositorio, _base_datos_no_disponible)
    app.add_exception_handler(StarletteHTTPException, _error_http)
    app.add_exception_handler(Exception, _error_interno)
