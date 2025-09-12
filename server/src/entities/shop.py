"""
Shop Entity for Marketplace Connections (Etsy, Shopify, etc.)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from ..database.core import Base

class Shop(Base):
    __tablename__ = 'shops'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Marketplace information
    provider = Column(String(50), nullable=False, default='etsy')  # 'etsy', 'shopify', etc.
    provider_shop_id = Column(String(255), nullable=False)
    display_name = Column(String(255))
    
    # OAuth tokens (consider encrypting these in production)
    access_token = Column(String(500))
    refresh_token = Column(String(500))
    token_expires_at = Column(DateTime)
    
    # Sync information
    last_sync_at = Column(DateTime)
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Unique constraint to prevent duplicate shops per org
    __table_args__ = (
        UniqueConstraint('org_id', 'provider', 'provider_shop_id'),
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="shops")
    
    def __repr__(self):
        return f"<Shop(id={self.id}, provider={self.provider}, shop_id={self.provider_shop_id})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'org_id': str(self.org_id),
            'provider': self.provider,
            'provider_shop_id': self.provider_shop_id,
            'display_name': self.display_name,
            'has_access_token': bool(self.access_token),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_token_valid(self) -> bool:
        """Check if the access token is still valid"""
        if not self.access_token:
            return False
        if not self.token_expires_at:
            return True  # No expiry set, assume valid
        return datetime.now(timezone.utc) < self.token_expires_at