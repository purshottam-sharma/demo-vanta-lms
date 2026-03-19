"""FastAPI dependencies for authentication."""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..db import get_db
from .models import UserPublic
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db=Depends(get_db),
) -> UserPublic:
    """Validate Bearer token and return the authenticated user.

    Raises HTTP 401 with specific detail messages:
    - "Not authenticated" when no / malformed token is provided.
    - "Token expired" when the token has expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_str = decode_access_token(credentials.credentials)
    except ValueError as exc:
        detail = str(exc)  # "Token expired" or "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    row = await db.fetchrow(
        "SELECT id, email, full_name, is_active, role FROM users WHERE id = $1",
        uuid.UUID(user_id_str),
    )
    if row is None or not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserPublic(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        is_active=row["is_active"],
        role=row["role"],
    )
