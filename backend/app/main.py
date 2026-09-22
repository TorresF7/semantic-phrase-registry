"""Raíz de composición: el único módulo que importa adaptadores concretos."""

from fastapi import FastAPI

from app.adapters.api.routers import salud

app = FastAPI(title="Banco de Frases")
app.include_router(salud.router, prefix="/api/v1")
