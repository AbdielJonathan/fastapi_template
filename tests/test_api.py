"""Tests de integración de los endpoints ``/usuarios`` y ``/health``."""


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_create_user(client):
    resp = await client.post(
        "/usuarios", json={"name": "Ada", "email": "ada@example.com"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["name"] == "Ada"
    assert body["email"] == "ada@example.com"
    assert body["is_active"] is True
    assert "created_at" in body


async def test_create_user_invalid_email(client):
    resp = await client.post(
        "/usuarios", json={"name": "Bad", "email": "not-an-email"}
    )
    assert resp.status_code == 422


async def test_create_duplicate_email_conflict(client):
    payload = {"name": "Dup", "email": "dup@example.com"}
    first = await client.post("/usuarios", json=payload)
    assert first.status_code == 201
    second = await client.post("/usuarios", json=payload)
    assert second.status_code == 409


async def test_list_users(client):
    await client.post("/usuarios", json={"name": "A", "email": "a@example.com"})
    await client.post("/usuarios", json={"name": "B", "email": "b@example.com"})

    resp = await client.get("/usuarios")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    paged = await client.get("/usuarios", params={"skip": 1, "limit": 1})
    assert paged.status_code == 200
    assert len(paged.json()) == 1


async def test_get_user(client):
    created = await client.post(
        "/usuarios", json={"name": "Grace", "email": "grace@example.com"}
    )
    user_id = created.json()["id"]

    resp = await client.get(f"/usuarios/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "grace@example.com"


async def test_get_user_not_found(client):
    resp = await client.get("/usuarios/999")
    assert resp.status_code == 404


async def test_update_user(client):
    created = await client.post(
        "/usuarios", json={"name": "Old", "email": "old@example.com"}
    )
    user_id = created.json()["id"]

    resp = await client.patch(
        f"/usuarios/{user_id}", json={"name": "New", "is_active": False}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "New"
    assert body["is_active"] is False
    assert body["email"] == "old@example.com"


async def test_update_user_not_found(client):
    resp = await client.patch("/usuarios/999", json={"name": "X"})
    assert resp.status_code == 404


async def test_update_user_duplicate_email_conflict(client):
    a = await client.post("/usuarios", json={"name": "A", "email": "a@example.com"})
    await client.post("/usuarios", json={"name": "B", "email": "b@example.com"})
    a_id = a.json()["id"]

    resp = await client.patch(f"/usuarios/{a_id}", json={"email": "b@example.com"})
    assert resp.status_code == 409


async def test_delete_user(client):
    created = await client.post(
        "/usuarios", json={"name": "Bye", "email": "bye@example.com"}
    )
    user_id = created.json()["id"]

    resp = await client.delete(f"/usuarios/{user_id}")
    assert resp.status_code == 204

    missing = await client.get(f"/usuarios/{user_id}")
    assert missing.status_code == 404


async def test_delete_user_not_found(client):
    resp = await client.delete("/usuarios/999")
    assert resp.status_code == 404
