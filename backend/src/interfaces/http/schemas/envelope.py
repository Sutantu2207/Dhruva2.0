"""Dhruva.AI V2 — Standardized API Response & Error Envelopes.

Strictly complies with Architecture Section 7:
- Standard Success Envelope: {"success": true, "data": ..., "meta": ...}
- Standard Error Envelope: {"success": false, "error": {"code": ..., "message": ..., "details": ..., "requestId": ...}}
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1)
    total_records: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=0)


class ResponseMeta(BaseModel):
    request_id: str = Field(description="Unique request correlation identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pagination: Optional[PaginationMeta] = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard success API envelope."""
    success: bool = True
    data: T
    meta: ResponseMeta


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[Dict[str, Any]] = Field(default_factory=list)
    request_id: str


class ApiErrorResponse(BaseModel):
    """Standard error API envelope."""
    success: bool = False
    error: ErrorBody
