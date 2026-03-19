"""Business logic for authentication flows."""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from asyncpg import Connection, UniqueViolationError
from fastapi import HTTPException, status

from ..config import settings
from .models import RegisterRequest, RegisterResponse
from .security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

FORGOT_PASSWORD_MESSAGE = (
    "If that email is registered you will receive a reset link."
)

# Valid bcrypt hash used for constant-time dummy verification when email
# is not found - prevents timing-based user enumeration attacks.
_DUMMY_HASH = "$2b$12$k34YGdNAb4xJm2t7wkme9.ljCJNOJj775Jfq4XFvWM9eg6DzW2dsS"


def _hash_token(token: str) -> str:
    """SHA-256 hash a token before storing it in the DB."""
    return hashlib.sha256(token.encode()).hexdigest()


async def register_user(db: Connection, payload: RegisterRequest) -> RegisterResponse:
    """Create a new user account.

    Raises:
        409 if the email is already registered.
    """
    hashed = hash_password(payload.password)
    user_id = uuid.uuid4()
    try:
        row = await db.fetchrow(
            """
            INSERT INTO users (id, email, hashed_password, full_name)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, full_name
            """,
            user_id,
            payload.email.lower(),
            hashed,
            payload.full_name,
        )
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return RegisterResponse(id=row["id"], email=row["email"], full_name=row["full_name"])


async def login_user(
    db: Connection, email: str, password: str
) -> tuple[str, str]:
    """Authenticate user and return (access_token, refresh_token).

    Raises:
        401 with identical message for wrong password or non-existent email
        (prevents user enumeration).
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    row = await db.fetchrow(
        "SELECT id, hashed_password, is_active FROM users WHERE email = $1",
        email.lower(),
    )
    if row is None:
        # Constant-time dummy verify to prevent timing-based enumeration
        verify_password("dummy", _DUMMY_HASH)
        raise _invalid

    if not verify_password(password, row["hashed_password"]):
        raise _invalid

    if not row["is_active"]:
        raise _invalid

    user_id = str(row["id"])
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # Persist hashed refresh token
    token_hash = _hash_token(refresh_token)
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await db.execute(
        """
        INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
        VALUES ($1, $2, $3, $4)
        """,
        uuid.uuid4(),
        row["id"],
        token_hash,
        expires_at,
    )

    return access_token, refresh_token


async def refresh_access_token(db: Connection, refresh_token: str) -> str:
    """Validate refresh token cookie and issue new access token.

    Raises:
        401 if token is missing, expired, or not found in DB.
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        user_id_str = decode_refresh_token(refresh_token)
    except ValueError:
        raise _invalid

    token_hash = _hash_token(refresh_token)
    row = await db.fetchrow(
        """
        SELECT id FROM refresh_tokens
        WHERE token_hash = $1
          AND expires_at > now()
        """,
        token_hash,
    )
    if row is None:
        raise _invalid

    return create_access_token(user_id_str)


async def logout_user(db: Connection, refresh_token: str | None) -> None:
    """Invalidate the refresh token in the DB (no-op if not found)."""
    if refresh_token:
        token_hash = _hash_token(refresh_token)
        await db.execute(
            "DELETE FROM refresh_tokens WHERE token_hash = $1",
            token_hash,
        )


async def forgot_password(db: Connection, email: str) -> str:
    """Initiate password reset (always returns same message to prevent enumeration)."""
    await db.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        email.lower(),
    )
    return FORGOT_PASSWORD_MESSAGE


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------


async def google_oauth_callback(
    db: Connection, code: str, redirect_uri: str
) -> tuple[str, str]:
    """Exchange Google auth code for tokens, upsert user, return JWT pair."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        google_access_token = token_data["access_token"]

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

    return await _oauth_upsert(
        db,
        provider="google",
        provider_user_id=userinfo["id"],
        email=userinfo["email"],
        full_name=userinfo.get("name", userinfo["email"]),
        access_token=google_access_token,
    )


async def apple_oauth_callback(
    db: Connection, code: str, redirect_uri: str
) -> tuple[str, str]:
    """Exchange Apple auth code for tokens, upsert user, return JWT pair."""
    import base64
    import json as _json

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://appleid.apple.com/auth/token",
            data={
                "code": code,
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": settings.APPLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

    id_token = token_data["id_token"]
    payload_b64 = id_token.split(".")[1]
    padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
    apple_payload = _json.loads(base64.urlsafe_b64decode(padded))

    email = apple_payload.get("email", "")
    return await _oauth_upsert(
        db,
        provider="apple",
        provider_user_id=apple_payload["sub"],
        email=email,
        full_name=email.split("@")[0] if email else apple_payload["sub"],
        access_token=token_data.get("access_token", ""),
    )


async def _oauth_upsert(
    db: Connection,
    *,
    provider: str,
    provider_user_id: str,
    email: str,
    full_name: str,
    access_token: str,
) -> tuple[str, str]:
    """Upsert oauth_accounts + users rows, return (jwt_access, jwt_refresh)."""
    existing = await db.fetchrow(
        """
        SELECT u.id, u.is_active
        FROM oauth_accounts oa
        JOIN users u ON u.id = oa.user_id
        WHERE oa.provider = $1 AND oa.provider_user_id = $2
        """,
        provider,
        provider_user_id,
    )

    if existing is not None:
        user_id = existing["id"]
        await db.execute(
            """
            UPDATE oauth_accounts SET access_token = $1
            WHERE provider = $2 AND provider_user_id = $3
            """,
            access_token,
            provider,
            provider_user_id,
        )
    else:
        user_row = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            email.lower(),
        )
        if user_row:
            user_id = user_row["id"]
        else:
            user_id = uuid.uuid4()
            await db.execute(
                """
                INSERT INTO users (id, email, full_name)
                VALUES ($1, $2, $3)
                """,
                user_id,
                email.lower(),
                full_name,
            )

        await db.execute(
            """
            INSERT INTO oauth_accounts (id, user_id, provider, provider_user_id, access_token)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (provider, provider_user_id)
            DO UPDATE SET access_token = EXCLUDED.access_token
            """,
            uuid.uuid4(),
            user_id,
            provider,
            provider_user_id,
            access_token,
        )

    jwt_access = create_access_token(str(user_id))
    jwt_refresh = create_refresh_token(str(user_id))

    token_hash = _hash_token(jwt_refresh)
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await db.execute(
        """
        INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
        VALUES ($1, $2, $3, $4)
        """,
        uuid.uuid4(),
        user_id,
        token_hash,
        expires_at,
    )

    return jwt_access, jwt_refresh
