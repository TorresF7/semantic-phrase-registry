"""Esquema inicial: extensión vector, tipo estado_frase, tabla frases e índices.

Traducción literal del DDL del plan §2. Es la primera y única migración.

Revision ID: 0001
Revises:
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fijo en el esquema, no leído de EMBEDDING_DIMENSION: una migración describe
# el esquema de un momento y no puede cambiar con la configuración. Si la
# dimensión del modelo no coincide, el arranque falla (B-14).
DIMENSION_EMBEDDING = 384

estado_frase = postgresql.ENUM(
    "UNICA", "DUPLICADO_CONFIRMADO", name="estado_frase", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    estado_frase.create(op.get_bind())

    op.create_table(
        "frases",
        # BigInteger + primary_key se emite como BIGSERIAL en PostgreSQL.
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("texto_original", sa.Text(), nullable=False),
        sa.Column("texto_normalizado", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(DIMENSION_EMBEDDING), nullable=False),
        sa.Column("estado", estado_frase, nullable=False),
        sa.Column("puntaje_similitud", sa.Double(), nullable=True),
        sa.Column("id_mas_parecida", sa.BigInteger(), sa.ForeignKey("frases.id"), nullable=True),
        sa.Column("modelo", sa.Text(), nullable=False),
        sa.Column("umbral_aplicado", sa.Double(), nullable=False),
        sa.Column(
            "creada_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_frases_texto_normalizado", "frases", ["texto_normalizado", "id"])
    op.create_index(
        "idx_frases_creada_en",
        "frases",
        [sa.text("creada_en DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "idx_frases_embedding",
        "frases",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    # DROP TABLE elimina también sus índices.
    op.drop_table("frases")
    # drop_table no elimina el tipo: sin esto el siguiente upgrade falla (plan §2).
    estado_frase.drop(op.get_bind())
    # La extensión se conserva: puede ser compartida y el upgrade usa IF NOT EXISTS.
