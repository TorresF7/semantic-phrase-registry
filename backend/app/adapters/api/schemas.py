"""Schemas de entrada y salida de la API (plan §1). Distintos de las entidades del dominio."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, StrictBool, field_serializer

from app.domain.entidades import EstadoFrase, Frase, MotivoDuplicado, ResultadoValidacion

# Tope defensivo sobre el texto crudo, para no normalizar entradas gigantes. La
# longitud de negocio (RN-01) la aplica el dominio sobre el texto normalizado.
TOPE_TEXTO_CRUDO = 2000


def _redondear(puntaje: float | None) -> float | None:
    """El redondeo es solo de presentación: la política compara sin redondear (RN-05)."""
    return None if puntaje is None else round(puntaje, 4)


class SolicitudValidacion(BaseModel):
    texto: str = Field(max_length=TOPE_TEXTO_CRUDO)


class SolicitudGuardado(SolicitudValidacion):
    # Estricto: "true" o 1 no cuentan como confirmación explícita (RN-12, AC-02b).
    confirmar_duplicado: StrictBool = False


class FraseResumen(BaseModel):
    id: int
    texto: str


class ResultadoValidacionRespuesta(BaseModel):
    es_posible_duplicado: bool
    motivo: MotivoDuplicado | None
    puntaje: float | None
    umbral_aplicado: float
    mas_parecida: FraseResumen | None
    modelo: str

    @field_serializer("puntaje")
    def _serializar_puntaje(self, puntaje: float | None) -> float | None:
        return _redondear(puntaje)

    @classmethod
    def desde_resultado(cls, resultado: ResultadoValidacion) -> "ResultadoValidacionRespuesta":
        mas_parecida = resultado.mas_parecida
        return cls(
            es_posible_duplicado=resultado.es_posible_duplicado,
            motivo=resultado.motivo,
            puntaje=resultado.puntaje,
            umbral_aplicado=resultado.umbral_aplicado,
            mas_parecida=None
            if mas_parecida is None
            else FraseResumen(id=mas_parecida.id, texto=mas_parecida.texto_original),
            modelo=resultado.modelo,
        )


class FraseRespuesta(BaseModel):
    id: int
    texto: str
    estado: EstadoFrase
    puntaje_similitud: float | None
    id_mas_parecida: int | None
    umbral_aplicado: float
    modelo: str
    creada_en: datetime

    @field_serializer("puntaje_similitud")
    def _serializar_puntaje(self, puntaje: float | None) -> float | None:
        return _redondear(puntaje)

    @classmethod
    def desde_frase(cls, frase: Frase) -> "FraseRespuesta":
        return cls(
            id=frase.id,
            texto=frase.texto_original,
            estado=frase.estado,
            puntaje_similitud=frase.puntaje_similitud,
            id_mas_parecida=frase.id_mas_parecida,
            umbral_aplicado=frase.umbral_aplicado,
            modelo=frase.modelo,
            creada_en=frase.creada_en,
        )


class ErrorRespuesta(BaseModel):
    """Forma uniforme de todo error (RN-16, plan §1.5)."""

    codigo: str
    mensaje: str
    detalles: dict[str, Any] | None = None
