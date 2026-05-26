"""Testes da rota de autenticação. Tudo que toca Neo4j é mockado.

Cobre registro, login e /me — a base da pirâmide de testes (§7.2: unitários de
endpoints da API).
"""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


class _FakeUser:
    uid = "user-1"
    name = "Ana Oliveira"
    email = "ana@x.com"
    is_active = True


def test_register_creates_user_when_email_is_new():
    with patch("app.api.routes.auth.User") as MockUser, patch(
        "app.api.routes.auth.get_password_hash", return_value="hashed"
    ):
        MockUser.nodes.get_or_none.return_value = None
        MockUser.return_value.save.return_value = _FakeUser()

        client = TestClient(app)
        r = client.post(
            "/api/auth/register",
            json={"name": "Ana Oliveira", "email": "ana@x.com", "password": "segredo123"},
        )

    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "ana@x.com"
    assert body["uid"] == "user-1"
    assert "password" not in body and "hashed_password" not in body


def test_register_rejects_duplicate_email():
    with patch("app.api.routes.auth.User") as MockUser:
        MockUser.nodes.get_or_none.return_value = _FakeUser()  # já existe

        client = TestClient(app)
        r = client.post(
            "/api/auth/register",
            json={"name": "Ana", "email": "ana@x.com", "password": "segredo123"},
        )

    assert r.status_code == 400
    assert r.json()["detail"] == "Email already registered"


def test_login_returns_bearer_token_on_valid_credentials():
    user = MagicMock(email="ana@x.com", hashed_password="hashed")
    with patch("app.api.routes.auth.User") as MockUser, patch(
        "app.api.routes.auth.verify_password", return_value=True
    ):
        MockUser.nodes.get_or_none.return_value = user

        client = TestClient(app)
        r = client.post(
            "/api/auth/login",
            data={"username": "ana@x.com", "password": "segredo123"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password():
    user = MagicMock(email="ana@x.com", hashed_password="hashed")
    with patch("app.api.routes.auth.User") as MockUser, patch(
        "app.api.routes.auth.verify_password", return_value=False
    ):
        MockUser.nodes.get_or_none.return_value = user

        client = TestClient(app)
        r = client.post(
            "/api/auth/login",
            data={"username": "ana@x.com", "password": "errada"},
        )

    assert r.status_code == 401


def test_login_rejects_unknown_user():
    with patch("app.api.routes.auth.User") as MockUser:
        MockUser.nodes.get_or_none.return_value = None

        client = TestClient(app)
        r = client.post(
            "/api/auth/login",
            data={"username": "ninguem@x.com", "password": "x"},
        )

    assert r.status_code == 401


def test_me_requires_auth():
    client = TestClient(app)
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user():
    from app.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    try:
        client = TestClient(app)
        r = client.get("/api/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.json()["email"] == "ana@x.com"
