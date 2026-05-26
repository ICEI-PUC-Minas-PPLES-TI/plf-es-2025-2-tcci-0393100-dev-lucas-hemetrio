"""Testes da rota de documentos. Neo4j e Storage são mockados.

Cobre upload (US 01), listagem e URL assinada. O caso de tipo inválido encoda a
regra de aceitação TA-02 ("Formato não suportado. Apenas PDF").
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.storage import get_storage


def _document(uid="d-1", title="artigo.pdf"):
    return SimpleNamespace(
        uid=uid,
        title=title,
        file_path=f"projects/p-1/{uid}.pdf",
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        pages=SimpleNamespace(all=lambda: []),
        save=MagicMock(),
    )


def _user_with_project(documents=None):
    project = MagicMock()
    project.uid = "p-1"
    project.documents.all.return_value = documents or []
    user = MagicMock()
    user.projects.all.return_value = [project]
    return user, project


def _fake_storage():
    storage = MagicMock()
    storage.get_presigned_url.return_value = "https://signed.example/doc.pdf"
    return storage


def test_upload_requires_auth(fake_pdf_bytes):
    client = TestClient(app)
    r = client.post(
        "/api/projects/p-1/documents",
        files={"file": ("artigo.pdf", fake_pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 401


def test_upload_valid_pdf_creates_processing_document(fake_pdf_bytes):
    user, project = _user_with_project()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        with patch("app.api.routes.documents.Document") as MockDocument, patch(
            "app.api.routes.documents.process_document"
        ):
            MockDocument.return_value.save.return_value = _document()
            client = TestClient(app)
            r = client.post(
                "/api/projects/p-1/documents",
                files={"file": ("artigo.pdf", fake_pdf_bytes, "application/pdf")},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "PROCESSING"
    assert body["page_count"] == 0
    project.documents.connect.assert_called_once()


def test_upload_rejects_non_pdf(fake_png_bytes):
    """TA-02: formato não suportado deve falhar com 400 e não persistir."""
    user, project = _user_with_project()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        client = TestClient(app)
        r = client.post(
            "/api/projects/p-1/documents",
            files={"file": ("imagem.png", fake_png_bytes, "image/png")},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]
    project.documents.connect.assert_not_called()


def test_list_documents_returns_them():
    user, _ = _user_with_project(documents=[_document(uid="d-1"), _document(uid="d-2")])
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app)
        r = client.get("/api/projects/p-1/documents")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_document_url_returns_signed_link():
    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        client = TestClient(app)
        r = client.get("/api/projects/p-1/documents/d-1/url")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.json()["url"].startswith("https://")


def test_get_document_url_404_for_unknown_doc():
    user, _ = _user_with_project(documents=[])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        client = TestClient(app)
        r = client.get("/api/projects/p-1/documents/missing/url")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 404
