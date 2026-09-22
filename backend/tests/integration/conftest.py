"""Fixtures y utilidades de los tests de integración de T-09.

Los tests de este paquete están marcados `integration` (plan §7, tasks.md
T-09): no corren en la suite rápida y necesitan `docker compose up -d db` con
la base `banco_frases_test` creada y migrada con
`bash scripts/preparar_base_test.sh`. `migrations/env.py` lee `url_base_datos`
(`DATABASE_URL`), no `url_base_datos_test`, así que **no** se ejecuta Alembic
desde estos fixtures: el script apunta `DATABASE_URL` a la base de test solo
para esa invocación.

Los adaptadores concretos (`app.adapters.persistence...`) se importan dentro
del cuerpo de las fixtures, nunca a nivel de módulo. Así, mientras T-09 no
esté implementada, la suite rápida —que solo *deselecciona* los tests
`integration*`, pero igualmente recolecta (importa) este módulo— no se rompe
por un `ModuleNotFoundError` en la fase de recolección.

`obtener_configuracion()` se usa tal cual, sin `_env_file=None`: a diferencia
de los tests unitarios de `test_config.py`, aquí sí queremos que
`TEST_DATABASE_URL` pueda venir del `.env` de quien desarrolla (D-14 es una
convención de los tests de `Configuracion`, no de estos fixtures). Si la
variable no está definida se usa el valor por defecto de
`architecture.md`, y si la base no responde el test falla con el error real:
no hay salto silencioso (skill `testing`, que solo permite `pytest.skip` por
ausencia de la propia variable, y aquí siempre hay un valor).
"""

from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from app.config import obtener_configuracion
from app.domain.entidades import EstadoFrase, FraseNueva
from app.domain.normalizacion import normalizar

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

    from app.adapters.persistence.repositorio import RepositorioPostgres

# La migración 0001 fija la columna `embedding` en `vector(384)` (plan §2):
# los vectores de prueba usan la misma dimensión para poder insertarse.
DIMENSION_EMBEDDING = 384

# Puerto que nadie escucha en localhost: usado para simular la base caída
# (RN-15). `connect_timeout=1` evita que el test espere el timeout de TCP por
# defecto del sistema operativo.
_URL_INACCESIBLE = (
    "postgresql+psycopg://banco:banco@localhost:1/banco_frases_test?connect_timeout=1"
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def fabrica_sesiones() -> "sessionmaker[Session]":
    """Fábrica de sesiones contra `banco_frases_test`, construida una sola vez."""
    from app.adapters.persistence.sesion import crear_fabrica_sesiones

    return crear_fabrica_sesiones(obtener_configuracion().url_base_datos_test)


@pytest.fixture(autouse=True)
def _tabla_frases_vacia(fabrica_sesiones: "sessionmaker[Session]") -> None:
    """Dejar la tabla vacía antes de cada test: ninguno depende de otro (skill testing)."""
    with fabrica_sesiones() as sesion:
        sesion.execute(text("TRUNCATE TABLE frases RESTART IDENTITY"))
        sesion.commit()


@pytest.fixture
def sesion_sql(fabrica_sesiones: "sessionmaker[Session]") -> Iterator["Session"]:
    """Sesión para preparar datos o leer filas con SQL directo dentro de un test."""
    with fabrica_sesiones() as sesion:
        yield sesion


@pytest.fixture
def repositorio(fabrica_sesiones: "sessionmaker[Session]") -> "RepositorioPostgres":
    from app.adapters.persistence.repositorio import RepositorioPostgres

    return RepositorioPostgres(fabrica_sesiones=fabrica_sesiones)


@pytest.fixture
def fabrica_sesiones_inaccesible() -> "sessionmaker[Session]":
    from app.adapters.persistence.sesion import crear_fabrica_sesiones

    return crear_fabrica_sesiones(_URL_INACCESIBLE)


@pytest.fixture
def repositorio_inaccesible(
    fabrica_sesiones_inaccesible: "sessionmaker[Session]",
) -> "RepositorioPostgres":
    from app.adapters.persistence.repositorio import RepositorioPostgres

    return RepositorioPostgres(fabrica_sesiones=fabrica_sesiones_inaccesible)


# --------------------------------------------------------------------------
# Utilidades para construir datos de prueba (vectores de 384 dimensiones)
# --------------------------------------------------------------------------


def vector_unitario(eje: int, dimension: int = DIMENSION_EMBEDDING) -> list[float]:
    """Vector con un 1.0 en `eje` y ceros en el resto. Norma 1 (RN-19)."""
    vector = [0.0] * dimension
    vector[eje] = 1.0
    return vector


def vector_con_coseno(
    coseno: float,
    *,
    eje_base: int = 0,
    eje_ortogonal: int = 1,
    dimension: int = DIMENSION_EMBEDDING,
) -> list[float]:
    """Vector unitario cuyo coseno con `vector_unitario(eje_base)` es exactamente `coseno`.

    Misma construcción que `FakeEmbedder.fijar_similitud` (tests/dobles): al
    ser ambos vectores unitarios y ortogonales los ejes salvo `eje_base`, el
    coseno entre ellos es `coseno` por definición, sin depender de ningún
    modelo real.
    """
    if not -1.0 <= coseno <= 1.0:
        raise ValueError(f"El coseno debe estar en [-1, 1]: {coseno}")
    vector = [0.0] * dimension
    vector[eje_base] = coseno
    vector[eje_ortogonal] = (1.0 - coseno * coseno) ** 0.5
    return vector


def frase_nueva(
    texto_original: str,
    embedding: list[float] | None = None,
    *,
    texto_normalizado: str | None = None,
    estado: EstadoFrase = EstadoFrase.UNICA,
    puntaje_similitud: float | None = None,
    id_mas_parecida: int | None = None,
    modelo: str = "modelo-de-prueba",
    umbral_aplicado: float = 0.80,
) -> FraseNueva:
    """Construye una `FraseNueva` lista para `repositorio.guardar(...)`."""
    return FraseNueva(
        texto_original=texto_original,
        texto_normalizado=texto_normalizado
        if texto_normalizado is not None
        else normalizar(texto_original),
        embedding=embedding if embedding is not None else vector_unitario(0),
        estado=estado,
        puntaje_similitud=puntaje_similitud,
        id_mas_parecida=id_mas_parecida,
        modelo=modelo,
        umbral_aplicado=umbral_aplicado,
    )


def vector_desde_columna(valor: str) -> list[float]:
    """Convierte el valor crudo de la columna `embedding` leída con SQL directo.

    Sin el adaptador de pgvector registrado en la conexión, psycopg devuelve el
    vector como texto `"[0.1,0.2,...]"`.
    """
    return [float(componente) for componente in valor.strip("[]").split(",")]
