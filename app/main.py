"""Punto de entrada de la aplicación FastAPI.

Configura el lifespan (crea las tablas al arranque), CORS, los routers y el
endpoint de health check para Cloud Run.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db import Base, engine
from app.routers import users

# from app.routers import tasks  # noqa: ERA001  (uso futuro, ver más abajo)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas al arranque y libera el engine al apagar.

    Se importan los modelos aquí para que queden registrados en `Base.metadata`
    antes de `create_all`.

    TODO: en producción, gestionar el esquema con Alembic (migraciones
    versionadas) en lugar de `create_all`, que no maneja cambios de esquema.
    """
    from app import models  # noqa: F401  registra los modelos en Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tablas verificadas/creadas al arranque.")

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
