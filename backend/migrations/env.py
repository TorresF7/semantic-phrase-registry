"""Entorno de Alembic.

La URL de la base sale de la configuración de la aplicación (DATABASE_URL),
nunca de alembic.ini. No hay `target_metadata`: la única migración se escribe a
mano contra el DDL del plan §2 y no se usa --autogenerate para el esquema
vectorial.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import obtener_configuracion

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", obtener_configuracion().url_base_datos)


def ejecutar_sin_conexion() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def ejecutar_con_conexion() -> None:
    motor = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with motor.connect() as conexion:
        context.configure(connection=conexion)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    ejecutar_sin_conexion()
else:
    ejecutar_con_conexion()
