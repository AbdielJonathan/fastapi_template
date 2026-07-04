"""Unit tests de las funciones del store contra la sesión de test."""

import pytest

from app import store
from app.dtos.user import UserCreate, UserUpdate


async def test_create_user(session):
    user = await store.create_user(
        session, UserCreate(name="Ada", email="ada@example.com")
    )
    assert user.id is not None
    assert user.name == "Ada"
    assert user.email == "ada@example.com"
    assert user.is_active is True
    assert user.created_at is not None


async def test_get_user(session):
    created = await store.create_user(
        session, UserCreate(name="Grace", email="grace@example.com")
    )
    fetched = await store.get_user(session, created.id)
    assert fetched is not None
    assert fetched.id == created.id


async def test_get_user_missing_returns_none(session):
    assert await store.get_user(session, 999) is None


async def test_list_users(session):
    await store.create_user(session, UserCreate(name="A", email="a@example.com"))
    await store.create_user(session, UserCreate(name="B", email="b@example.com"))

    users = await store.list_users(session)
    assert len(users) == 2

    page = await store.list_users(session, skip=1, limit=1)
    assert len(page) == 1


async def test_update_user(session):
    created = await store.create_user(
        session, UserCreate(name="Old", email="old@example.com")
    )
    updated = await store.update_user(
        session, created.id, UserUpdate(name="New", is_active=False)
    )
    assert updated is not None
    assert updated.name == "New"
    assert updated.is_active is False
    # El email no se tocó porque no venía en el update parcial.
    assert updated.email == "old@example.com"


async def test_update_user_missing_returns_none(session):
    result = await store.update_user(session, 999, UserUpdate(name="X"))
    assert result is None


async def test_delete_user(session):
    created = await store.create_user(
        session, UserCreate(name="Bye", email="bye@example.com")
    )
    assert await store.delete_user(session, created.id) is True
    assert await store.get_user(session, created.id) is None


async def test_delete_user_missing_returns_false(session):
    assert await store.delete_user(session, 999) is False


async def test_duplicate_email_raises(session):
    from sqlalchemy.exc import IntegrityError

    await store.create_user(session, UserCreate(name="One", email="dup@example.com"))
    with pytest.raises(IntegrityError):
        await store.create_user(
            session, UserCreate(name="Two", email="dup@example.com")
        )
