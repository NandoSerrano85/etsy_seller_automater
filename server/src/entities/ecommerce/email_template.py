"""Email Template entity for ecommerce email messaging system."""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from server.src.database.core import Base


class EmailTemplate(Base):
    """Email template for order confirmations, shipping notifications, and marketing."""

    __tablename__ = "ecommerce_email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Template metadata
    name = Column(String(255), nullable=False)
    template_type = Column(String(50), nullable=False)  # "transactional", "marketing"
    email_type = Column(String(50), nullable=False)  # "order_confirmation", "shipping_notification", "marketing"
    subject = Column(String(500), nullable=False)

    # Template content (JSON blocks for visual editor)
    blocks = Column(JSONB, default=[])

    # Branding settings
    primary_color = Column(String(7), default="#10b981")
    secondary_color = Column(String(7), default="#059669")
    logo_url = Column(String(512))

    # SendGrid integration
    sendgrid_template_id = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name={self.name}, email_type={self.email_type})>"
