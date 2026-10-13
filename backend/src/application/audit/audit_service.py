"""Dhruva.AI V2 — Audit Service.

Provides centralized recording of security-sensitive and governance actions.
Guarantees zero leakage of secrets (passwords, tokens).
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger, sanitize_payload
from src.domain.audit.models import AuditLog
from src.infrastructure.repositories.audit_repository import AuditRepository


class AuditService:
    """Application service for recording structured audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AuditRepository(session)

    async def log_event(
        self,
        action: str,
        entity_name: str,
        entity_id: Optional[uuid.UUID] = None,
        institution_id: Optional[uuid.UUID] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """Record an immutable audit log entry."""
        try:
            record = AuditLog(
                institution_id=institution_id,
                actor_user_id=actor_user_id,
                action=action,
                entity_name=entity_name,
                entity_id=entity_id,
                old_values=sanitize_payload(old_values) if old_values else None,
                new_values=sanitize_payload(new_values) if new_values else None,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
            )
            created = await self.repository.create(record)
            logger.info(
                f"Audit recorded: {action} on {entity_name}",
                extra={
                    "request_id": request_id,
                    "institution_id": institution_id,
                    "user_id": actor_user_id,
                    "operation": action,
                },
            )
            return created
        except Exception as exc:
            logger.error(
                f"Failed to record audit log for action '{action}': {str(exc)}",
                extra={"request_id": request_id},
            )
            return None

    # Alias for flexibility
    log_action = log_event
