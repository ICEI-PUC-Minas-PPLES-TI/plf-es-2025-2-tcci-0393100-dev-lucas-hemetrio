from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.search import SearchResponse
from app.services import search_service

router = APIRouter()


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., description="Termo de busca (>=2 chars não-whitespace)"),
    current_user: User = Depends(get_current_user),
):
    try:
        return search_service.search(user_uid=current_user.uid, query=q)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
