"""Entidades y objetos de valor del dominio (plan §3 y §4)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EstadoFrase(StrEnum):
    """Situación con la que quedó registrada una frase (RN-12)."""

    UNICA = "UNICA"
    DUPLICADO_CONFIRMADO = "DUPLICADO_CONFIRMADO"


class MotivoDuplicado(StrEnum):
    """Por qué se considera posible duplicado (RN-04, RN-05)."""

    EXACTO = "EXACTO"
    SEMANTICO = "SEMANTICO"


@dataclass(frozen=True, slots=True)
class Frase:
    """Frase ya persistida, con sus metadatos inmutables (RN-13).

    No transporta el embedding: nadie lo lee de vuelta.
    """

    id: int
    texto_original: str
    estado: EstadoFrase
    puntaje_similitud: float | None
    id_mas_parecida: int | None
    modelo: str
    umbral_aplicado: float
    creada_en: datetime


@dataclass(frozen=True, slots=True)
class FraseNueva:
    """Lo que se va a guardar. El `id` y la fecha los asigna la base (RN-13, RN-14)."""

    texto_original: str
    texto_normalizado: str
    embedding: list[float]
    estado: EstadoFrase
    puntaje_similitud: float | None
    id_mas_parecida: int | None
    modelo: str
    umbral_aplicado: float


@dataclass(frozen=True, slots=True)
class ResultadoValidacion:
    """Resultado de validar una frase (RN-05 a RN-09).

    `puntaje` está sin redondear: el redondeo es solo de presentación (RN-05).
    `texto_normalizado` y `embedding` son de uso interno entre casos de uso y
    no se serializan; `embedding` es `None` cuando el motivo es `EXACTO`.
    """

    es_posible_duplicado: bool
    motivo: MotivoDuplicado | None
    puntaje: float | None
    mas_parecida: Frase | None
    umbral_aplicado: float
    modelo: str
    texto_normalizado: str
    embedding: list[float] | None
