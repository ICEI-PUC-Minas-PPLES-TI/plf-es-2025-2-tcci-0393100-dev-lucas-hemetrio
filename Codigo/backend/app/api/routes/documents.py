import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.api.deps import get_current_user
from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.storage import get_storage
from app.storage.base import StorageBackend

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

    file_data = file.file.read()
    doc_uid = str(uuid.uuid4())
    object_name = f"projects/{project_uid}/{doc_uid}.pdf"

    storage.upload_file(file_data, object_name, "application/pdf")

    document = Document(
        uid=doc_uid,
        title=file.filename or "document.pdf",
        file_path=object_name,
        status=DocumentStatus.UPLOADING.value,
    ).save()

    project.documents.connect(document)
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    project_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    return sorted(project.documents.all(), key=lambda d: d.created_at, reverse=True)


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

    storage.delete_file(document.file_path)
    project.documents.disconnect(document)
    document.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
