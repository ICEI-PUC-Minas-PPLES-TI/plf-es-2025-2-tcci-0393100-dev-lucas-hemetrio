from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRename, ProjectResponse

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


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
):
    project = Project(name=project_in.name).save()
    current_user.projects.connect(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(current_user: User = Depends(get_current_user)):
    return sorted(
        current_user.projects.all(),
        key=lambda item: item.created_at,
        reverse=True,
    )


@router.patch("/{project_uid}", response_model=ProjectResponse)
def rename_project(
    project_uid: str,
    project_in: ProjectRename,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    project.name = project_in.name
    project.save()
    return project


@router.delete("/{project_uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_uid: str,
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(current_user, project_uid)
    current_user.projects.disconnect(project)
    project.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)