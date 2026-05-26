"""Testes da rota de anotações. Neo4j e Storage são mockados.

Cobre criação (US 03/US 04), listagem e remoção. O cenário de integração TI-01
no documento foi reescrito para este contrato REST (criar → aparecer em GET),
já que não há fila de sincronização offline.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.storage import get_storage


def _annotation(uid="a-1", title="Importante"):
    return SimpleNamespace(
        uid=uid,
        title=title,
        content="",
        position="",
        canvas_path=f"projects/p-1/annotations/{uid}.json",
        canvas_image_path="",
        document_uid=None,
        status="PROCESSING",
        extracted_text="",
        created_at=datetime.now(timezone.utc),
        save=MagicMock(),
        delete=MagicMock(),
    )


def _user_with_project(annotations=None):
    project = MagicMock()
    project.uid = "p-1"
    project.annotations.all.return_value = annotations or []
    project.documents.all.return_value = []
    user = MagicMock()
    user.projects.all.return_value = [project]
    return user, project


def test_create_requires_auth():
    client = TestClient(app)
    r = client.post("/api/projects/p-1/annotations", data={"title": "x", "canvas_data": "{}"})
    assert r.status_code == 401


def test_create_annotation_persists_and_returns_it():
    user, project = _user_with_project()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = lambda: MagicMock()
    try:
        with patch("app.api.routes.annotations.Annotation") as MockAnnotation, patch(
            "app.api.routes.annotations.process_annotation"
        ):
            MockAnnotation.return_value.save.return_value = _annotation(title="Revisar")
            client = TestClient(app)
            r = client.post(
                "/api/projects/p-1/annotations",
                data={"title": "Revisar", "canvas_data": "{\"strokes\":[]}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 201
    assert r.json()["title"] == "Revisar"
    project.annotations.connect.assert_called_once()


def test_list_annotations_returns_them():
    user, _ = _user_with_project(annotations=[_annotation(uid="a-1"), _annotation(uid="a-2")])
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app)
        r = client.get("/api/projects/p-1/annotations")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_annotation_removes_it_from_system():
    """TA-06 (adaptado): remoção tira a anotação do sistema (não há banco local)."""
    annotation = _annotation(uid="a-1")
    user, project = _user_with_project(annotations=[annotation])
    storage = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        client = TestClient(app)
        r = client.delete("/api/projects/p-1/annotations/a-1")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 204
    storage.delete_file.assert_called_once_with(annotation.canvas_path)
    project.annotations.disconnect.assert_called_once_with(annotation)
    annotation.delete.assert_called_once()


def test_delete_unknown_annotation_returns_404():
    user, _ = _user_with_project(annotations=[])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = lambda: MagicMock()
    try:
        client = TestClient(app)
        r = client.delete("/api/projects/p-1/annotations/missing")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 404
