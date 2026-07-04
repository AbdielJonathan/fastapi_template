"""Fixtures de test.

Por defecto se usa SQLite en memoria (`sqlite+aiosqlite://`): cero infra,
rápido y portable. Como `db.py` arma la URL de producción desde `settings`, aquí
se crea un engine de test independiente y se hace override de `get_session` para
inyectar la sesión de test en la app.

Para correr contra MySQL real (motor de producción), exporta
`TEST_DATABASE_URL`, p. ej.:
    TEST_DATABASE_URL="mysql+asyncmy://user:pass@127.0.0.1:3306/test" uv run pytest
"""

import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  registra los modelos en Base.metadata
from app.db import Base, get_session
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite://")


def _make_engine():
    """Crea un engine de test; con SQLite en memoria comparte una sola conexión.

    `StaticPool` + `check_same_thread=False` mantiene la misma conexión in-memory
    entre sesiones para que las tablas creadas persistan durante el test.
    """
    if TEST_DATABASE_URL.startswith("sqlite"):
        return create_async_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_async_engine(TEST_DATABASE_URL)


@pytest_asyncio.fixture
async def engine():
    eng = _make_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Sesión de test para los unit tests del store."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest_asyncio.fixture
async def client(engine):
    """AsyncClient con `get_session` sobrescrito para apuntar al engine de test."""
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()
