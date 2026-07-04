"""Lógica de negocio: CRUD de usuarios sobre la base de datos.

Funciones async que reciben una `AsyncSession` explícita (nada de sesión
global). Trabajan con el modelo ORM `User` y reciben DTOs como entrada. No
contienen lógica HTTP: devuelven `None`/`False` cuando no encuentran, y el
router traduce esos casos a 404.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dtos.user import UserCreate, UserUpdate
from app.models import User


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Crea y persiste un usuario.

    Puede levantar `IntegrityError` si el email ya existe; el router lo traduce
    a 409.
    """
    user = User(name=data.name, email=data.email)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Devuelve el usuario por id, o `None` si no existe."""
    return await session.get(User, user_id)


async def list_users(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[User]:
    """Lista usuarios con paginación simple."""
    result = await session.execute(
        select(User).order_by(User.id).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def update_user(
    session: AsyncSession, user_id: int, data: UserUpdate
) -> User | None:
    """Actualiza parcialmente un usuario; devuelve `None` si no existe.

    Puede levantar `IntegrityError` si el nuevo email colisiona con otro.
    """
    user = await session.get(User, user_id)
    if user is None:
        return None

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """Elimina un usuario; devuelve `True` si existía, `False` si no."""
    user = await session.get(User, user_id)
    if user is None:
        return False

    await session.delete(user)
    await session.commit()
    return True
