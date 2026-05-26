"""Testes das rotas de mentions/co-occurrences. Nenhum teste toca Neo4j."""
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


class _FakeUser:
    uid = "user-1"
    email = "u@x.com"


def _mock_user():
    return _FakeUser()


def _project_mock(uid="p-1"):
    p = MagicMock()
    p.uid = uid
    return p


def test_mentions_requires_auth():
    client = TestClient(app)
    r = client.get("/api/projects/p-1/knowledge-graph/nodes/n-1/mentions")
    assert r.status_code == 401


def test_mentions_404_when_project_not_owned():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            side_effect=HTTPException(status_code=404, detail="Project not found"),
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/nodes/n-1/mentions")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_mentions_404_when_node_not_in_project():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            return_value=_project_mock(),
        ), patch(
            "app.api.routes.knowledge._query_node_summary",
            return_value=None,
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/nodes/n-missing/mentions")
        assert r.status_code == 404
        assert r.json()["detail"] == "Node not found"
    finally:
        app.dependency_overrides.clear()


def test_mentions_200_returns_list():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        node_summary = ("n-1", "PER", "Beauchamp", 12)
        rows = [
            ("m-1", "Beauchamp e Childress propuseram...", "document",
             "doc-1", "Bioética - Cap 1", 3),
            ("m-2", "na obra de Childress e Beauchamp...", "annotation",
             "ann-1", "Anotação 2", None),
        ]
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            return_value=_project_mock(),
        ), patch(
            "app.api.routes.knowledge._query_node_summary",
            return_value=node_summary,
        ), patch(
            "app.api.routes.knowledge._query_mentions_by_node",
            return_value=rows,
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/nodes/n-1/mentions")
        assert r.status_code == 200
        body = r.json()
        assert body["node"] == {
            "uid": "n-1", "label": "PER", "text": "Beauchamp", "mention_count": 12,
        }
        assert len(body["mentions"]) == 2
        assert body["mentions"][0]["source_type"] == "document"
        assert body["mentions"][0]["page_number"] == 3
        assert body["mentions"][1]["source_type"] == "annotation"
        assert body["mentions"][1]["page_number"] is None
    finally:
        app.dependency_overrides.clear()


def test_mentions_200_empty_when_node_has_no_mentions():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            return_value=_project_mock(),
        ), patch(
            "app.api.routes.knowledge._query_node_summary",
            return_value=("n-1", "ORG", "Kennedy Institute", 0),
        ), patch(
            "app.api.routes.knowledge._query_mentions_by_node",
            return_value=[],
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/nodes/n-1/mentions")
        assert r.status_code == 200
        assert r.json()["mentions"] == []
    finally:
        app.dependency_overrides.clear()


def test_co_occurrences_requires_auth():
    client = TestClient(app)
    r = client.get("/api/projects/p-1/knowledge-graph/edges/a-1/b-1/co-occurrences")
    assert r.status_code == 401


def test_co_occurrences_404_when_project_not_owned():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            side_effect=HTTPException(status_code=404, detail="Project not found"),
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/edges/a-1/b-1/co-occurrences")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_co_occurrences_404_when_edge_missing():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            return_value=_project_mock(),
        ), patch(
            "app.api.routes.knowledge._query_edge_summary",
            return_value=None,
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/edges/a-1/b-1/co-occurrences")
        assert r.status_code == 404
        assert r.json()["detail"] == "Edge not found"
    finally:
        app.dependency_overrides.clear()


def test_co_occurrences_200_returns_list():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        edge_summary = (
            ("a-1", "PER", "Beauchamp", 12),
            ("b-1", "PER", "Childress", 9),
            8,
        )
        rows = [
            (None, "Beauchamp e Childress propuseram...", "document",
             "doc-1", "Bioética", 3),
            (None, "Childress e Beauchamp afirmam...", "annotation",
             "ann-1", "Anotação X", None),
        ]
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            return_value=_project_mock(),
        ), patch(
            "app.api.routes.knowledge._query_edge_summary",
            return_value=edge_summary,
        ), patch(
            "app.api.routes.knowledge._query_co_occurrences",
            return_value=rows,
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/edges/a-1/b-1/co-occurrences")
        assert r.status_code == 200
        body = r.json()
        assert body["weight"] == 8
        assert body["node_a"]["text"] == "Beauchamp"
        assert body["node_b"]["text"] == "Childress"
        assert len(body["co_occurrences"]) == 2
        assert "uid" not in body["co_occurrences"][0]
    finally:
        app.dependency_overrides.clear()


def test_co_occurrences_accepts_reversed_order():
    """Backend normaliza (a,b) → ordem canônica; chamada com (b,a) também resolve."""
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    captured = {}

    def fake_edge_summary(project_uid, a, b):
        captured["pair"] = (a, b)
        return (
            ("a-1", "PER", "Beauchamp", 12),
            ("b-1", "PER", "Childress", 9),
            8,
        )

    try:
        with patch(
            "app.api.routes.knowledge._get_owned_project",
            return_value=_project_mock(),
        ), patch(
            "app.api.routes.knowledge._query_edge_summary",
            side_effect=fake_edge_summary,
        ), patch(
            "app.api.routes.knowledge._query_co_occurrences",
            return_value=[],
        ):
            client = TestClient(app)
            r = client.get("/api/projects/p-1/knowledge-graph/edges/b-1/a-1/co-occurrences")
        assert r.status_code == 200
        assert captured["pair"] == ("a-1", "b-1")
    finally:
        app.dependency_overrides.clear()
