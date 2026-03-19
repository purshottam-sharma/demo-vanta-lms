"""Pydantic models for admin user management endpoints."""
from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool


class PaginatedUsersResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    page: int
    page_size: int


class UpdateRoleRequest(BaseModel):
    role: UserRole


class UpdateStatusRequest(BaseModel):
    is_active: bool
