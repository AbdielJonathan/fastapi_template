"""Configuración de la base de datos (SOLO infraestructura de DB).

Contiene el engine async, la fábrica de sesiones, la clase declarativa `Base` y
la dependencia `get_session`. Aquí NO se definen modelos (viven en `models.py`)
ni lógica de negocio (vive en `store.py`).

Importante para evitar ciclos de import: `db.py` no importa `models.py`. Es
`models.py` quien importa `Base` desde aquí, y el `create_all` del lifespan
importa los modelos en el punto donde se usan.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import settings


def _build_database_url() -> str:
    """Arma la URL async de conexión a MySQL a partir de campos discretos.

    Formato: ``mysql+asyncmy://USER:PASSWORD@HOST:PORT/NAME``.

    Cloud SQL vía unix socket: si `DB_HOSTNAME` es una ruta de socket
    (p. ej. ``/cloudsql/PROJECT:REGION:INSTANCE``), asyncmy la acepta como
    parámetro ``unix_socket`` en la query string.
    """
    if settings.DB_HOSTNAME.startswith("/"):
        # Conexión por unix socket (Cloud SQL).
        return (
            f"mysql+asyncmy://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@/"
            f"{settings.DB_NAME}?unix_socket={settings.DB_HOSTNAME}"
        )
    return (
        f"mysql+asyncmy://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOSTNAME}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


DATABASE_URL = _build_database_url()

# `create_async_engine` no abre conexiones hasta que se usan, así que importar
# este módulo es seguro aunque la DB no esté disponible (p. ej. en tests).
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: entrega una `AsyncSession` por request."""
    async with AsyncSessionLocal() as session:
        yield session
