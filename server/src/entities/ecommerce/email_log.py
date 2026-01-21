"""Email Log entity for tracking sent emails and delivery status."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from server.src.database.core import Base


class EmailLog(Base):
    """Log of all sent emails with delivery tracking."""

    __tablename__ = "ecommerce_email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Email details
    template_id = Column(UUID(as_uuid=True), ForeignKey("ecommerce_email_templates.id", ondelete="SET NULL"))
    email_type = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)

    # Related entities
    order_id = Column(UUID(as_uuid=True), ForeignKey("ecommerce_orders.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("ecommerce_customers.id", ondelete="SET NULL"), nullable=True)

    # SendGrid tracking
    sendgrid_message_id = Column(String(255))
    sendgrid_status = Column(String(50))  # "sent", "delivered", "opened", "clicked", "bounced"

    # Delivery tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)

    # Error tracking
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EmailLog(id={self.id}, recipient={self.recipient_email}, type={self.email_type}, status={self.sendgrid_status})>"
