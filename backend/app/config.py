"""Configuración por variables de entorno (Artículo 6).

Los nombres de las variables son los de `docs/context/architecture.md`; los
campos siguen el vocabulario del glosario. Un valor fuera de rango hace fallar
la construcción: el proceso no arranca con una configuración inválida (B-24).

`HF_HOME` no está aquí a propósito: la lee `huggingface_hub` directamente del
entorno y la aplicación nunca la consulta (Artículo 7).
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Solo para desarrollo sin Docker: el .env vive en la raíz del repositorio,
# junto a docker-compose.yml. En Compose las variables llegan ya como entorno
# del proceso y este archivo no existe dentro de la imagen.
_ARCHIVO_ENV = Path(__file__).resolve().parents[2] / ".env"


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ARCHIVO_ENV,
        env_file_encoding="utf-8",
        # El .env también trae variables de Compose y del frontend.
        extra="ignore",
        frozen=True,
    )

    url_base_datos: str = Field(
        default="postgresql+psycopg://banco:banco@localhost:5432/banco_frases",
        validation_alias="DATABASE_URL",
    )
    url_base_datos_test: str = Field(
        default="postgresql+psycopg://banco:banco@localhost:5432/banco_frases_test",
        validation_alias="TEST_DATABASE_URL",
    )
    # Calibrado en T-11 con scripts/calibrar_umbral.py (D-07, D-20).
    umbral_similitud: float = Field(
        default=0.75, ge=0.0, le=1.0, validation_alias="SIMILARITY_THRESHOLD"
    )
    nombre_modelo: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        min_length=1,
        validation_alias="EMBEDDING_MODEL_NAME",
    )
    dimension_embedding: int = Field(default=384, gt=0, validation_alias="EMBEDDING_DIMENSION")
    # RN-01: el mínimo de una frase es 3, así que el máximo no puede ser menor.
    longitud_maxima_frase: int = Field(default=280, ge=3, validation_alias="MAX_PHRASE_LENGTH")
    origenes_cors: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:5173"], validation_alias="CORS_ORIGINS"
    )
    nivel_log: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", validation_alias="LOG_LEVEL"
    )

    @field_validator("origenes_cors", mode="before")
    @classmethod
    def _separar_por_comas(cls, valor: object) -> object:
        if isinstance(valor, str):
            return [origen.strip() for origen in valor.split(",") if origen.strip()]
        return valor

    @field_validator("nivel_log", mode="before")
    @classmethod
    def _nivel_en_mayusculas(cls, valor: object) -> object:
        return valor.upper() if isinstance(valor, str) else valor


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
