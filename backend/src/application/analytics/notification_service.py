"""Dhruva.AI V2 — Notification Hub Application Service.

Handles:
- In-app notification creation & delivery.
- User-bound recipient isolation.
- Unread count aggregation and batch state transitions.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from src.domain.analytics.models import Notification
from src.infrastructure.persistence.postgres.base import utc_now


class NotificationService:
    """Application service for real-time in-app alerts and notifications."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self,
        institution_id: uuid.UUID,
        recipient_user_id: uuid.UUID,
        notification_type: str,
        title: str,
        message: str,
        link_url: str = "",
        actor_user_id: Optional[uuid.UUID] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create and dispatch an in-app notification to a specific recipient."""
        if not title or len(title.strip()) < 2:
            raise ValidationError("Notification title must be at least 2 characters.")

        notification = Notification(
            id=uuid.uuid4(),
            institution_id=institution_id,
            recipient_user_id=recipient_user_id,
            actor_user_id=actor_user_id,
            notification_type=notification_type.upper().strip(),
            title=title.strip(),
            message=message.strip(),
            link_url=link_url.strip(),
            is_read=False,
            metadata_json=metadata_json or {},
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def list_user_notifications(
        self,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Fetch notifications strictly scoped to recipient_user_id."""
        stmt = select(Notification).where(
            and_(
                Notification.institution_id == institution_id,
                Notification.recipient_user_id == user_id,
            )
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)

        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        notifications = list(res.scalars().all())

        # Compute unread count
        count_stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.institution_id == institution_id,
                Notification.recipient_user_id == user_id,
                Notification.is_read == False,
            )
        )
        unread_count = (await self.session.execute(count_stmt)).scalar_one()

        return {
            "notifications": notifications,
            "unread_count": unread_count,
            "total_records": len(notifications),
        }

    async def mark_as_read(
        self,
        institution_id: uuid.UUID,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Notification:
        """Mark a notification as read with ownership verification."""
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.institution_id == institution_id,
            )
        )
        notification = (await self.session.execute(stmt)).scalar_one_or_none()
        if not notification:
            raise NotFoundError(f"Notification '{notification_id}' not found.")

        if notification.recipient_user_id != user_id:
            raise PermissionDeniedError("Cannot modify another user's notification.")

        notification.is_read = True
        notification.read_at = utc_now()
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def mark_all_as_read(
        self,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """Batch mark all unread notifications for a user."""
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.institution_id == institution_id,
                    Notification.recipient_user_id == user_id,
                    Notification.is_read == False,
                )
            )
            .values(is_read=True, read_at=utc_now())
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount
