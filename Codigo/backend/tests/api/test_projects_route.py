"""Testes da rota de projetos. Neo4j é mockado via fake current_user + patch do
modelo Project. Cobre o CRUD de projetos (US 02) na camada de unidade.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app


def _project(uid="p-1", name="História", created_at=None):
    return SimpleNamespace(
        uid=uid,
        name=name,
        created_at=created_at or datetime.now(timezone.utc),
        save=MagicMock(),
        delete=MagicMock(),
    )


def _fake_user_with(projects):
    user = MagicMock()
    user.projects.all.return_value = projects
    return user


def test_list_requires_auth():
    client = TestClient(app)
    r = client.get("/api/projects")
    assert r.status_code == 401


def test_create_project_persists_and_returns_it():
    user = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch("app.api.routes.projects.Project") as MockProject:
            MockProject.return_value.save.return_value = _project(name="Dissertação")
            client = TestClient(app)
            r = client.post("/api/projects", json={"name": "Dissertação"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 201
    assert r.json()["name"] == "Dissertação"
    user.projects.connect.assert_called_once()


def test_list_projects_returns_newest_first():
    now = datetime.now(timezone.utc)
    older = _project(uid="p-old", name="Antigo", created_at=now - timedelta(days=1))
    newer = _project(uid="p-new", name="Novo", created_at=now)
    app.dependency_overrides[get_current_user] = lambda: _fake_user_with([older, newer])
    try:
        client = TestClient(app)
        r = client.get("/api/projects")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    uids = [p["uid"] for p in r.json()]
    assert uids == ["p-new", "p-old"]


def test_rename_project_updates_name():
    project = _project(uid="p-1", name="Velho")
    app.dependency_overrides[get_current_user] = lambda: _fake_user_with([project])
    try:
        client = TestClient(app)
        r = client.patch("/api/projects/p-1", json={"name": "Novo Nome"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.json()["name"] == "Novo Nome"
    assert project.name == "Novo Nome"
    project.save.assert_called_once()


def test_rename_unknown_project_returns_404():
    app.dependency_overrides[get_current_user] = lambda: _fake_user_with([])
    try:
        client = TestClient(app)
        r = client.patch("/api/projects/missing", json={"name": "x"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 404


def test_delete_project_disconnects_and_deletes():
    project = _project(uid="p-1")
    user = _fake_user_with([project])
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app)
        r = client.delete("/api/projects/p-1")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 204
    user.projects.disconnect.assert_called_once_with(project)
    project.delete.assert_called_once()
