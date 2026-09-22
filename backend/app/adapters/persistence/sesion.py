"""Motor y fábrica de sesiones síncronas con `psycopg` 3 (D-10)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def crear_fabrica_sesiones(url: str) -> sessionmaker[Session]:
    motor = create_engine(
        url,
        # Descarta conexiones muertas del pool antes de usarlas: tras una caída
        # de la base, la siguiente petición no falla por una conexión vieja.
        pool_pre_ping=True,
        # Las fechas vuelven siempre en UTC, sea cual sea la zona del servidor.
        connect_args={"options": "-c timezone=UTC"},
    )
    return sessionmaker(motor, expire_on_commit=False)
