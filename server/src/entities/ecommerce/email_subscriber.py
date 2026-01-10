"""Email Subscriber entity for managing marketing email subscribers."""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from server.src.database.core import Base


class EmailSubscriber(Base):
    """Marketing email subscriber with segmentation and analytics."""

    __tablename__ = "ecommerce_email_subscribers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Subscriber info
    email = Column(String(255), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("ecommerce_customers.id", ondelete="SET NULL"), nullable=True)

    # Subscription status
    is_subscribed = Column(Boolean, default=True)
    unsubscribed_at = Column(DateTime)

    # Segmentation tags
    tags = Column(JSONB, default=[])  # ["vip", "new_customer", "inactive"]

    # Analytics
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    last_sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'email', name='uq_user_subscriber_email'),
    )

    def __repr__(self):
        return f"<EmailSubscriber(id={self.id}, email={self.email}, subscribed={self.is_subscribed})>"
