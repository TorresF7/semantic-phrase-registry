"""Ejemplos para `/docs`: cada código de cada endpoint lleva uno (DoD de T-12b).

Los mensajes de error salen de `errores.py`, así que la documentación no puede
desincronizarse del comportamiento real.
"""

from typing import Any

from app.adapters.api.errores import (
    MENSAJE_BASE_DATOS,
    MENSAJE_IA,
    MENSAJE_INTERNO,
    MENSAJE_PARAMETROS,
)
from app.adapters.api.schemas import ErrorRespuesta, EstadoSalud

_MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_MAS_PARECIDA = {"id": 42, "texto": "El pago fue rechazado por el banco"}

EJEMPLO_VALIDACION = {
    "es_posible_duplicado": True,
    "motivo": "SEMANTICO",
    "puntaje": 0.8735,
    "umbral_aplicado": 0.75,
    "mas_parecida": _MAS_PARECIDA,
    "modelo": _MODELO,
}
EJEMPLO_FRASE = {
    "id": 43,
    "texto": "La entidad bancaria rechazó la transacción",
    "estado": "DUPLICADO_CONFIRMADO",
    "puntaje_similitud": 0.8735,
    "id_mas_parecida": 42,
    "umbral_aplicado": 0.75,
    "modelo": _MODELO,
    "creada_en": "2026-09-22T17:04:33Z",
}
EJEMPLO_PAGINA = {
    "total": 25,
    "limite": 20,
    "desplazamiento": 0,
    "items": [
        {
            "id": 43,
            "texto": "La entidad bancaria rechazó la transacción",
            "estado": "DUPLICADO_CONFIRMADO",
            "puntaje_similitud": 0.8735,
            "mas_parecida": {"id": 12, "texto": "El pago fue rechazado por el banco"},
            "creada_en": "2026-09-22T17:04:33Z",
        }
    ],
}

_MENSAJE_LONGITUD = "La frase no puede tener más de 280 caracteres."

# Código → (estado HTTP, mensaje, detalles).
_ERRORES: dict[str, tuple[int, str, dict[str, Any] | None]] = {
    "FRASE_INVALIDA": (422, _MENSAJE_LONGITUD, {"texto": _MENSAJE_LONGITUD}),
    "PARAMETROS_INVALIDOS": (422, MENSAJE_PARAMETROS, {"texto": "Campo obligatorio."}),
    "POSIBLE_DUPLICADO": (
        409,
        "Ya existe una frase muy parecida a la que intentas guardar.",
        {
            "puntaje": 0.8735,
            "umbral_aplicado": 0.75,
            "motivo": "SEMANTICO",
            "mas_parecida": _MAS_PARECIDA,
        },
    ),
    "ERROR_INTERNO": (500, MENSAJE_INTERNO, None),
    "SERVICIO_IA_NO_DISPONIBLE": (503, MENSAJE_IA, None),
    "BASE_DATOS_NO_DISPONIBLE": (503, MENSAJE_BASE_DATOS, None),
}


def _ejemplo_error(codigo: str, detalles_parametros: dict[str, str] | None) -> dict[str, Any]:
    _, mensaje, detalles = _ERRORES[codigo]
    if codigo == "PARAMETROS_INVALIDOS" and detalles_parametros is not None:
        detalles = dict(detalles_parametros)
    valor: dict[str, Any] = {"codigo": codigo, "mensaje": mensaje}
    if detalles is not None:
        valor["detalles"] = detalles
    return {"summary": codigo, "value": valor}


def exito(ejemplo: dict[str, Any]) -> dict[str, Any]:
    return {"content": {"application/json": {"example": ejemplo}}}


def errores(
    *codigos: str, detalles_parametros: dict[str, str] | None = None
) -> dict[int | str, dict[str, Any]]:
    """`responses` de FastAPI con un ejemplo por código de error, agrupados por estado.

    `detalles_parametros` sustituye el ejemplo de `PARAMETROS_INVALIDOS`, que por
    defecto nombra el campo `texto`, para los endpoints que no lo reciben.
    """
    respuestas: dict[int | str, dict[str, Any]] = {}
    for codigo in codigos:
        estado = _ERRORES[codigo][0]
        respuesta = respuestas.setdefault(
            estado,
            {
                "model": ErrorRespuesta,
                "description": "",
                "content": {"application/json": {"examples": {}}},
            },
        )
        respuesta["description"] = " o ".join(filter(None, [respuesta["description"], codigo]))
        ejemplos = respuesta["content"]["application/json"]["examples"]
        ejemplos[codigo] = _ejemplo_error(codigo, detalles_parametros)
    return respuestas


RESPUESTAS_SALUD: dict[int | str, dict[str, Any]] = {
    200: exito({"estado": "ok", "modelo_cargado": True, "base_datos": "ok"}),
    503: {
        "model": EstadoSalud,
        "description": "Modelo sin cargar o base de datos no disponible",
        "content": {
            "application/json": {
                "example": {"estado": "degradado", "modelo_cargado": False, "base_datos": "ok"}
            }
        },
    },
}
