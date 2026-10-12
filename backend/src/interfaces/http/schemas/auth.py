"""Dhruva.AI V2 — Authentication & Identity Schemas."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from src.domain.identity.roles import SystemRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class RoleResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    permissions: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: uuid.UUID
    institution_id: Optional[uuid.UUID] = None
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    status: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponseData(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshResponseData(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    role: SystemRole = SystemRole.STUDENT
    phone: Optional[str] = Field(default=None, max_length=32)
