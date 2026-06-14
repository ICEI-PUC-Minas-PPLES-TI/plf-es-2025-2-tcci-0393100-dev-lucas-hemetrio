import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.storage import get_storage
from app.storage.base import StorageBackend
from app.worker import spawn_worker

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_owned_project(current_user: User, project_uid: str) -> Project:
    project = next(
        (item for item in current_user.projects.all() if item.uid == project_uid),
        None,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def _build_response(document: Document) -> dict:
    return {
        "uid": document.uid,
        "title": document.title,
        "file_path": document.file_path,
        "status": document.status,
        "created_at": document.created_at,
        "page_count": len(document.pages.all()),
    }


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    project_uid: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    doc_uid = str(uuid.uuid4())
    object_name = f"projects/{project_uid}/{doc_uid}.pdf"

    # Streaming direto para o MinIO, sem carregar o PDF inteiro na memória.
    file.file.seek(0, 2)
    length = file.file.tell()
    file.file.seek(0)
    storage.upload_stream(file.file, object_name, length, "application/pdf")

    document = Document(
        uid=doc_uid,
        title=file.filename or "document.pdf",
        file_path=object_name,
        status=DocumentStatus.PROCESSING.value,
    ).save()

    project.documents.connect(document)

    # Processamento pesado em subprocesso separado, para não travar o servidor.
    try:
        spawn_worker("document", doc_uid)
    except Exception:  # noqa: BLE001
        logger.exception("falha ao iniciar worker para doc_uid=%s", doc_uid)
        document.status = DocumentStatus.FAILED.value
        document.save()

    return _build_response(document)


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    project_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    sorted_docs = sorted(project.documents.all(), key=lambda d: d.created_at, reverse=True)
    return [_build_response(d) for d in sorted_docs]


@router.get("/{doc_uid}/url")
def get_document_url(
    project_uid: str,
    doc_uid: str,
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)
    document = next(
        (d for d in project.documents.all() if d.uid == doc_uid),
        None,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    url = storage.get_presigned_url(document.file_path)
    return {"url": url}


def _parse_range(range_header: str, size: int) -> tuple[int, int] | None:
    """Parse um header HTTP Range simples para (start, end) inclusivo.

    Suporta `bytes=start-end`, `bytes=start-` e `bytes=-suffix` (cauda — usada pelo
    pdf.js para ler o xref). Retorna None se inválido ou não-satisfazível.
    """
    if not range_header.startswith("bytes="):
        return None
    spec = range_header[len("bytes=") :].split(",")[0].strip()
    if "-" not in spec:
        return None
    start_s, end_s = spec.split("-", 1)
    try:
        if start_s == "":
            suffix = int(end_s)
            if suffix <= 0:
                return None
            start = max(0, size - suffix)
            end = size - 1
        else:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
            end = min(end, size - 1)
    except ValueError:
        return None
    if start > end or start >= size:
        return None
    return start, end


@router.get("/{doc_uid}/stream")
def stream_document(
    project_uid: str,
    doc_uid: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)
    document = next(
        (d for d in project.documents.all() if d.uid == doc_uid),
        None,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    size = storage.stat_file(document.file_path)
    base_headers = {
        "Content-Disposition": f'inline; filename="{document.title}"',
        "Accept-Ranges": "bytes",
    }

    # Carregamento progressivo: o pdf.js pede só os trechos necessários via Range,
    # mostrando a primeira página sem baixar o PDF inteiro.
    range_header = request.headers.get("range")
    if range_header:
        parsed = _parse_range(range_header, size)
        if parsed is None:
            return Response(
                status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                headers={"Content-Range": f"bytes */{size}", "Accept-Ranges": "bytes"},
            )
        start, end = parsed
        length = end - start + 1
        return StreamingResponse(
            storage.stream_range(document.file_path, start, length),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type="application/pdf",
            headers={
                **base_headers,
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Content-Length": str(length),
            },
        )

    return StreamingResponse(
        storage.stream_file(document.file_path),
        media_type="application/pdf",
        headers={**base_headers, "Content-Length": str(size)},
    )


@router.post("/{doc_uid}/reprocess", status_code=status.HTTP_202_ACCEPTED)
def reprocess_document(
    project_uid: str,
    doc_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    document = next(
        (d for d in project.documents.all() if d.uid == doc_uid),
        None,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document.status = DocumentStatus.PROCESSING.value
    document.save()

    try:
        spawn_worker("document", doc_uid)
    except Exception:  # noqa: BLE001
        logger.exception("falha ao iniciar worker para reprocess doc_uid=%s", doc_uid)
        document.status = DocumentStatus.FAILED.value
        document.save()
    return {"status": "queued"}


@router.delete("/{doc_uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    project_uid: str,
    doc_uid: str,
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)
    document = next(
        (d for d in project.documents.all() if d.uid == doc_uid),
        None,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    for page in document.pages.all():
        document.pages.disconnect(page)
        page.delete()

    storage.delete_file(document.file_path)
    project.documents.disconnect(document)
    document.delete()

    # O grafo de conhecimento é agregado por projeto: remover o documento exige
    # reconstruir o grafo para não deixar entidades/menções órfãs.
    try:
        spawn_worker("rebuild", project_uid)
    except Exception:  # noqa: BLE001
        logger.exception(
            "falha ao iniciar rebuild do grafo após apagar doc_uid=%s", doc_uid
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
