"""Dhruva.AI V2 — Audit Log Schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    institution_id: Optional[uuid.UUID] = None
    actor_user_id: Optional[uuid.UUID] = None
    action: str
    entity_name: str
    entity_id: Optional[uuid.UUID] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
