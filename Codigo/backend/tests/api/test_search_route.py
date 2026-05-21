from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.search import SearchResponse


class _FakeUser:
    uid = "user-1"
    email = "u@x.com"


def _mock_user():
    return _FakeUser()


def test_search_endpoint_requires_auth():
    client = TestClient(app)
    r = client.get("/api/search?q=redes")
    assert r.status_code == 401


def test_search_endpoint_returns_400_on_short_query():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user
    try:
        client = TestClient(app)
        r = client.get("/api/search?q=a")
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_search_endpoint_happy_path():
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = _mock_user

    fake_response = SearchResponse(query="redes", total=0, results_by_project=[])
    try:
        with patch("app.api.routes.search.search_service.search", return_value=fake_response):
            client = TestClient(app)
            r = client.get("/api/search?q=redes")
        assert r.status_code == 200
        body = r.json()
        assert body["query"] == "redes"
        assert body["total"] == 0
        assert body["results_by_project"] == []
    finally:
        app.dependency_overrides.clear()
