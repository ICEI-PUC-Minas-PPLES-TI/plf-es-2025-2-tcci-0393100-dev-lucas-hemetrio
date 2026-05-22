"""Testes das rotas de knowledge-graph. Tudo que toca Neo4j é mockado."""
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


class _FakeUser:
    uid = "user-1"
    email = "u@x.com"


def _mock_user():
    return _FakeUser()


def _project_mock(uid="p-1", status="DONE", updated_at=None):
    p = MagicMock()
    p.uid = uid
    p.knowledge_status = status
    p.knowledge_updated_at = updated_at
    return p


def test_get_requires_auth():
    client = TestClient(app)
    r = client.get("/api/projects/p-1/knowledge-graph")
    assert r.status_code == 401


def test_get_404_when_project_not_owned():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            side_effect=HTTPException(status_code=404, detail="Project not found"),
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_done_returns_payload():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user

    project = _project_mock(status="DONE")
    fake_nodes = [
        ["n-1", "PER", "Lula", 3],
        ["n-2", "LOC", "Brasil", 5],
    ]
    fake_edges = [["n-1", "n-2", 2]]

    try:
        with patch("app.api.routes.knowledge._get_owned_project", return_value=project), \
             patch("app.api.routes.knowledge._query_nodes", return_value=fake_nodes), \
             patch("app.api.routes.knowledge._query_edges", return_value=fake_edges):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "DONE"
        assert len(body["nodes"]) == 2
        assert len(body["edges"]) == 1
        assert body["edges"][0]["weight"] == 2
    finally:
        app.dependency_overrides.clear()


def test_get_processing_returns_202():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user

    project = _project_mock(status="PROCESSING")
    try:
        with patch("app.api.routes.knowledge._get_owned_project", return_value=project):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph")
        assert r.status_code == 202
        body = r.json()
        assert body["status"] == "PROCESSING"
        assert body["nodes"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_failed_returns_200_with_failed_status():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user

    project = _project_mock(status="FAILED")
    try:
        with patch("app.api.routes.knowledge._get_owned_project", return_value=project):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph")
        assert r.status_code == 200
        assert r.json()["status"] == "FAILED"
    finally:
        app.dependency_overrides.clear()


def test_post_rebuild_requires_auth():
    client = TestClient(app)
    r = client.post("/api/projects/p-1/rebuild-knowledge")
    assert r.status_code == 401


def test_post_rebuild_returns_202_and_schedules_task():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user

    project = _project_mock()
    try:
        with patch("app.api.routes.knowledge._get_owned_project", return_value=project), \
             patch("app.api.routes.knowledge.rebuild_project_knowledge") as task:
            client = TestClient(app)
            r = client.post("/api/projects/p-1/rebuild-knowledge")
        assert r.status_code == 202
        task.assert_called_once_with("p-1")
    finally:
        app.dependency_overrides.clear()
