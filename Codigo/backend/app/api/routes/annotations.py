import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status

from app.api.deps import get_current_user
from app.models.annotation import Annotation, AnnotationType
from app.models.project import Project
from app.models.user import User
from app.schemas.annotation import AnnotationResponse
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


@router.get("", response_model=list[AnnotationResponse])
def list_annotations(
    project_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    return sorted(project.annotations.all(), key=lambda a: a.created_at, reverse=True)


@router.post("", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
def create_annotation(
    project_uid: str,
    title: str = Form(...),
    type: str = Form(default=AnnotationType.HANDWRITING.value),
    position: str = Form(default=""),
    document_uid: str | None = Form(default=None),
    canvas_data: str = Form(...),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)

    ann_uid = str(uuid.uuid4())
    object_name = f"projects/{project_uid}/annotations/{ann_uid}.json"

    storage.upload_file(canvas_data.encode("utf-8"), object_name, "application/json")

    annotation = Annotation(
        uid=ann_uid,
        title=title,
        type=type,
        canvas_path=object_name,
        position=position,
        document_uid=document_uid,
    ).save()

    project.annotations.connect(annotation)

    if document_uid:
        doc = next(
            (d for d in project.documents.all() if d.uid == document_uid),
            None,
        )
        if doc:
            doc.annotations.connect(annotation)

    return annotation


@router.get("/{ann_uid}/canvas")
def get_annotation_canvas(
    project_uid: str,
    ann_uid: str,
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)
    annotation = next(
        (a for a in project.annotations.all() if a.uid == ann_uid),
        None,
    )
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found",
        )
    raw = storage.read_file(annotation.canvas_path)
    return {"canvas_data": raw.decode("utf-8")}


@router.patch("/{ann_uid}/canvas", response_model=AnnotationResponse)
def update_annotation_canvas(
    project_uid: str,
    ann_uid: str,
    canvas_data: str = Form(...),
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)
    annotation = next(
        (a for a in project.annotations.all() if a.uid == ann_uid),
        None,
    )
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found",
        )
    storage.upload_file(canvas_data.encode("utf-8"), annotation.canvas_path, "application/json")
    return annotation


@router.delete("/{ann_uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_annotation(
    project_uid: str,
    ann_uid: str,
    current_user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    project = _get_owned_project(current_user, project_uid)
    annotation = next(
        (a for a in project.annotations.all() if a.uid == ann_uid),
        None,
    )
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found",
        )

    storage.delete_file(annotation.canvas_path)
    project.annotations.disconnect(annotation)
    annotation.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
