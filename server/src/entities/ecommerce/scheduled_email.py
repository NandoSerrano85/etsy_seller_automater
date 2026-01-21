"""Scheduled Email entity for managing marketing email campaigns."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from server.src.database.core import Base


class ScheduledEmail(Base):
    """Scheduled marketing email campaign with recipient filtering."""

    __tablename__ = "ecommerce_scheduled_emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("ecommerce_email_templates.id", ondelete="CASCADE"), nullable=False)

    # Recipient segmentation
    recipient_filter = Column(JSONB)  # {"tags": ["vip"], "last_order_days_ago": 30}
    recipient_count = Column(Integer)  # Calculated when scheduled

    # Scheduling
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")  # "pending", "sending", "sent", "failed", "cancelled"

    # Execution tracking
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduledEmail(id={self.id}, scheduled_for={self.scheduled_for}, status={self.status})>"
