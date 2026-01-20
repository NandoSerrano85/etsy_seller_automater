"""
Domain Verification Entity

Tracks domain verification attempts and status for custom domains.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.src.database.core import Base
from datetime import datetime
import uuid


class DomainVerification(Base):
    """Tracks domain verification attempts and status"""
    __tablename__ = "domain_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storefront_id = Column(Integer, ForeignKey('ecommerce_storefront_settings.id', ondelete='CASCADE'), nullable=False)

    # Domain being verified
    domain = Column(String(255), nullable=False)

    # Verification details
    verification_token = Column(String(64), nullable=False)
    verification_method = Column(String(20), nullable=False)  # "dns_txt" or "dns_cname"

    # Status tracking
    status = Column(String(20), default='pending')  # pending, verified, failed, expired
    attempts = Column(Integer, default=0)
    last_checked_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    storefront = relationship('StorefrontSettings', backref='domain_verifications')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "storefront_id": self.storefront_id,
            "domain": self.domain,
            "verification_token": self.verification_token,
            "verification_method": self.verification_method,
            "status": self.status,
            "attempts": self.attempts,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_expired(self) -> bool:
        """Check if verification has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
        return False

    def can_retry(self, max_attempts: int = 10) -> bool:
        """Check if more verification attempts are allowed"""
        return self.attempts < max_attempts and self.status not in ('verified', 'expired')
