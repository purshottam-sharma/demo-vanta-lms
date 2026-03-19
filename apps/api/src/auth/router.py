"""FastAPI router for /api/v1/auth endpoints."""
from __future__ import annotations

import logging
import urllib.parse

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from ..config import settings
from ..db import get_db
from .models import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from .service import (
    apple_oauth_callback,
    forgot_password,
    google_oauth_callback,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=REFRESH_COOKIE_MAX_AGE,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, db=Depends(get_db)) -> RegisterResponse:
    """Register a new user account."""
    return await register_user(db, payload)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest, response: Response, db=Depends(get_db)
) -> TokenResponse:
    """Authenticate with email + password."""
    access_token, refresh_token = await login_user(db, payload.email, payload.password)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db=Depends(get_db),
) -> MessageResponse:
    """Revoke refresh token and clear cookie."""
    await logout_user(db, refresh_token)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db=Depends(get_db),
) -> RefreshResponse:
    """Issue a new access token using the refresh token cookie."""
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    access_token = await refresh_access_token(db, refresh_token)
    return RefreshResponse(access_token=access_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def forgot_password_endpoint(
    payload: ForgotPasswordRequest, db=Depends(get_db)
) -> MessageResponse:
    """Initiate password reset flow."""
    message = await forgot_password(db, payload.email)
    return MessageResponse(message=message)


@router.get("/google", status_code=status.HTTP_302_FOUND)
async def google_login(request: Request) -> RedirectResponse:
    """Redirect to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    redirect_uri = str(request.url_for("google_callback"))
    params = urllib.parse.urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
    )
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/google/callback",
    response_model=TokenResponse,
    name="google_callback",
)
async def google_callback(
    code: str,
    request: Request,
    response: Response,
    db=Depends(get_db),
) -> TokenResponse:
    """Handle Google OAuth callback."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    redirect_uri = str(request.url_for("google_callback"))
    access_token, refresh_token = await google_oauth_callback(db, code, redirect_uri)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.get("/apple", status_code=status.HTTP_302_FOUND)
async def apple_login(request: Request) -> RedirectResponse:
    """Redirect to Apple OAuth consent screen."""
    if not settings.APPLE_CLIENT_ID or not settings.APPLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    redirect_uri = str(request.url_for("apple_callback"))
    params = urllib.parse.urlencode(
        {
            "client_id": settings.APPLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "name email",
            "response_mode": "form_post",
        }
    )
    return RedirectResponse(
        url=f"https://appleid.apple.com/auth/authorize?{params}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/apple/callback",
    response_model=TokenResponse,
    name="apple_callback",
)
async def apple_callback(
    code: str,
    request: Request,
    response: Response,
    db=Depends(get_db),
) -> TokenResponse:
    """Handle Apple OAuth callback."""
    if not settings.APPLE_CLIENT_ID or not settings.APPLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth not configured",
        )
    redirect_uri = str(request.url_for("apple_callback"))
    access_token, refresh_token = await apple_oauth_callback(db, code, redirect_uri)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)
