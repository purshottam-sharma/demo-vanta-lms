"""Admin router — user management endpoints under /admin."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.dependencies import get_current_user
from ..auth.models import UserPublic
from ..db import get_db
from .models import (
    AdminUserResponse,
    PaginatedUsersResponse,
    UpdateRoleRequest,
    UpdateStatusRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Dependency: admin-only gate
# ---------------------------------------------------------------------------


async def get_admin_user(
    current_user: UserPublic = Depends(get_current_user),
) -> UserPublic:
    """Raise 403 if the authenticated user is not an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ---------------------------------------------------------------------------
# GET /admin/users
# ---------------------------------------------------------------------------


@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    search: str = Query(default="", description="Filter by name or email (case-insensitive)"),
    role: str = Query(default="", description="Filter by role: student | instructor | admin"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    current_admin: UserPublic = Depends(get_admin_user),
    db=Depends(get_db),
) -> PaginatedUsersResponse:
    """Return a paginated, filterable list of all users (admin only)."""
    base_where = "WHERE 1=1"
    params: list = []
    param_index = 1

    if search:
        base_where += (
            f" AND (lower(full_name) LIKE lower(${param_index})"
            f" OR lower(email) LIKE lower(${param_index}))"
        )
        params.append(f"%{search}%")
        param_index += 1

    if role:
        base_where += f" AND role = ${param_index}"
        params.append(role)
        param_index += 1

    # Total count (no LIMIT/OFFSET)
    count_sql = f"SELECT COUNT(*) FROM users {base_where}"
    total: int = await db.fetchval(count_sql, *params)

    # Paginated data
    offset = (page - 1) * page_size
    data_sql = (
        f"SELECT id, email, full_name, role, is_active FROM users {base_where}"
        f" ORDER BY full_name ASC"
        f" LIMIT ${param_index} OFFSET ${param_index + 1}"
    )
    rows = await db.fetch(data_sql, *params, page_size, offset)

    items = [
        AdminUserResponse(
            id=row["id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=row["is_active"],
        )
        for row in rows
    ]

    return PaginatedUsersResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}/role
# ---------------------------------------------------------------------------


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    body: UpdateRoleRequest,
    current_admin: UserPublic = Depends(get_admin_user),
    db=Depends(get_db),
) -> AdminUserResponse:
    """Update the role of a user (admin only). Cannot change your own role."""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role",
        )

    row = await db.fetchrow(
        "SELECT id, email, full_name, role, is_active FROM users WHERE id = $1",
        user_id,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated = await db.fetchrow(
        "UPDATE users SET role = $1 WHERE id = $2"
        " RETURNING id, email, full_name, role, is_active",
        body.role.value,
        user_id,
    )

    return AdminUserResponse(
        id=updated["id"],
        email=updated["email"],
        full_name=updated["full_name"],
        role=updated["role"],
        is_active=updated["is_active"],
    )


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}/status
# ---------------------------------------------------------------------------


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    body: UpdateStatusRequest,
    current_admin: UserPublic = Depends(get_admin_user),
    db=Depends(get_db),
) -> AdminUserResponse:
    """Activate or deactivate a user (admin only)."""
    row = await db.fetchrow(
        "SELECT id, email, full_name, role, is_active FROM users WHERE id = $1",
        user_id,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated = await db.fetchrow(
        "UPDATE users SET is_active = $1 WHERE id = $2"
        " RETURNING id, email, full_name, role, is_active",
        body.is_active,
        user_id,
    )

    return AdminUserResponse(
        id=updated["id"],
        email=updated["email"],
        full_name=updated["full_name"],
        role=updated["role"],
        is_active=updated["is_active"],
    )
