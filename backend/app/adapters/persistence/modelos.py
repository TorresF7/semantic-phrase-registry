"""Modelo ORM de la tabla `frases` (plan §2).

Refleja la migración 0001, que es la fuente del esquema. No sale de
`adapters/persistence/`: el repositorio lo traduce a entidades de dominio.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Double, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.entidades import EstadoFrase

# Fijo en el esquema, igual que en la migración 0001 (B-14).
DIMENSION_EMBEDDING = 384


class Base(DeclarativeBase):
    pass


class ModeloFrase(Base):
    __tablename__ = "frases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    texto_original: Mapped[str] = mapped_column(Text)
    texto_normalizado: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSION_EMBEDDING))
    estado: Mapped[EstadoFrase] = mapped_column(
        ENUM(EstadoFrase, name="estado_frase", create_type=False)
    )
    puntaje_similitud: Mapped[float | None] = mapped_column(Double)
    id_mas_parecida: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("frases.id"))
    modelo: Mapped[str] = mapped_column(Text)
    umbral_aplicado: Mapped[float] = mapped_column(Double)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
