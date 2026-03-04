from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload: dict[str, Any] = decode_access_token(token)
    except JWTError:
        raise _credentials_exception

    email = payload.get("sub")
    if not email:
        raise _credentials_exception

    user = User.nodes.get_or_none(email=email)
    if not user or not user.is_active:
        raise _credentials_exception

    return user
