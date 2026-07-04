"""Punto de entrada de la aplicación FastAPI.

Configura el lifespan (ciclo de vida), CORS, los routers y el endpoint de health
check para Cloud Run.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db import engine
from app.routers import users

# from app.routers import tasks  # noqa: ERA001  (uso futuro, ver más abajo)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la app: libera el engine al apagar.

    El esquema de la DB lo gestiona **Alembic**, no la app: ejecuta
    `alembic upgrade head` antes/durante el deploy (ver README). La app ya no
    crea tablas al arrancar.
    """
    yield

    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
# app.include_router(tasks.router)  # noqa: ERA001  descomenta cuando /tareas tenga endpoints


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check para Cloud Run."""
    return {"status": "ok"}
