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
        delete=MagicMock(),
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
    storage.stat_file.return_value = 13
    storage.stream_file.return_value = iter([b"%PDF-1.4 body"])
    return storage


def test_upload_requires_auth(fake_pdf_bytes):
    client = TestClient(app)
    r = client.post(
        "/api/projects/p-1/documents",
        files={"file": ("artigo.pdf", fake_pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 401


def test_upload_valid_pdf_creates_processing_document(fake_pdf_bytes):
    """Upload é assíncrono: persiste PROCESSING e delega o pipeline ao worker em
    subprocesso, sem rodar OCR inline."""
    user, project = _user_with_project()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        with patch("app.api.routes.documents.Document") as MockDocument, patch(
            "app.api.routes.documents.spawn_worker"
        ) as mock_spawn:
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
    # delega ao worker em subprocesso, modo "document"
    assert mock_spawn.call_args.args[0] == "document"


def test_upload_marks_failed_when_worker_spawn_fails(fake_pdf_bytes):
    """Se o subprocesso não inicia, o documento não pode ficar preso em PROCESSING."""
    user, _ = _user_with_project()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    saved_doc = _document()
    try:
        with patch("app.api.routes.documents.Document") as MockDocument, patch(
            "app.api.routes.documents.spawn_worker", side_effect=OSError("no fork")
        ):
            MockDocument.return_value.save.return_value = saved_doc
            client = TestClient(app)
            r = client.post(
                "/api/projects/p-1/documents",
                files={"file": ("artigo.pdf", fake_pdf_bytes, "application/pdf")},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 201
    assert r.json()["status"] == "FAILED"


def test_reprocess_spawns_worker():
    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch("app.api.routes.documents.spawn_worker") as mock_spawn:
            client = TestClient(app)
            r = client.post("/api/projects/p-1/documents/d-1/reprocess")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 202
    mock_spawn.assert_called_once_with("document", "d-1")


def test_delete_triggers_graph_rebuild():
    """Apagar documento reconstrói o grafo do projeto — evita vértices órfãos."""
    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        with patch("app.api.routes.documents.spawn_worker") as mock_spawn:
            client = TestClient(app)
            r = client.delete("/api/projects/p-1/documents/d-1")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 204
    mock_spawn.assert_called_once_with("rebuild", "p-1")


def test_stream_returns_pdf_body():
    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        client = TestClient(app)
        r = client.get("/api/projects/p-1/documents/d-1/stream")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["accept-ranges"] == "bytes"
    assert r.content == b"%PDF-1.4 body"


def test_stream_exposes_range_headers_for_cors():
    """pdf.js (cross-origin no WebView) só usa carregamento progressivo se conseguir
    LER Accept-Ranges/Content-Range/Content-Length — exige expose_headers no CORS."""
    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = _fake_storage
    try:
        client = TestClient(app)
        r = client.get(
            "/api/projects/p-1/documents/d-1/stream",
            headers={"Origin": "http://localhost:3000"},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    exposed = r.headers.get("access-control-expose-headers", "")
    assert "Accept-Ranges" in exposed
    assert "Content-Range" in exposed


def test_stream_serves_partial_content_for_range():
    """Carregamento progressivo: um header Range retorna 206 com só o trecho pedido."""
    storage = _fake_storage()
    storage.stat_file.return_value = 100
    storage.stream_range.return_value = iter([b"slice"])

    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        client = TestClient(app)
        r = client.get(
            "/api/projects/p-1/documents/d-1/stream",
            headers={"Range": "bytes=0-4"},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 206
    assert r.headers["content-range"] == "bytes 0-4/100"
    assert r.headers["content-length"] == "5"
    assert r.content == b"slice"
    storage.stream_range.assert_called_once_with("projects/p-1/d-1.pdf", 0, 5)


def test_stream_returns_416_for_unsatisfiable_range():
    storage = _fake_storage()
    storage.stat_file.return_value = 100

    user, _ = _user_with_project(documents=[_document(uid="d-1")])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        client = TestClient(app)
        r = client.get(
            "/api/projects/p-1/documents/d-1/stream",
            headers={"Range": "bytes=999-1500"},
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 416
    assert r.headers["content-range"] == "bytes */100"


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
