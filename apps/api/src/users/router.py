"""Users router — exposes user-facing endpoints under /users."""
from fastapi import APIRouter, Depends

from ..auth.dependencies import get_current_user
from ..auth.models import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Return the currently authenticated user's public profile."""
    return current_user
