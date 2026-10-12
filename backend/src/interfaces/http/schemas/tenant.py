"""Dhruva.AI V2 — Tenant / Institution Schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InstitutionCreateRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    legal_name: str = Field(min_length=2, max_length=255)
    domain: Optional[str] = Field(default=None, max_length=255)


class InstitutionResponse(BaseModel):
    id: uuid.UUID
    slug: str
    legal_name: str
    domain: Optional[str] = None
    status: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
