from sqlalchemy import Column, DateTime, func, ForeignKey, Text, String, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
import enum

class PlatformType(enum.Enum):
    """Supported third-party platforms"""
    ETSY = "ETSY"
    SHOPIFY = "SHOPIFY"
    AMAZON = "AMAZON"
    EBAY = "EBAY"

class ConnectionType(enum.Enum):
    """Types of platform connections"""
    OAUTH2 = "oauth2"  # OAuth 2.0 with access/refresh tokens
    API_KEY = "api_key"  # Simple API key authentication
    BASIC_AUTH = "basic_auth"  # Username/password authentication

class PlatformConnection(Base):
    """
    Stores authentication/connection information for third-party platforms.
    Separates credentials from business/store information.
    """
    __tablename__ = 'platform_connections'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Platform identification
    platform = Column(Enum(PlatformType), nullable=False)
    connection_type = Column(Enum(ConnectionType), nullable=False, default=ConnectionType.OAUTH2)

    # Connection credentials (encrypted in production)
    access_token = Column(Text, nullable=True)  # OAuth access token or API key
    refresh_token = Column(Text, nullable=True)  # OAuth refresh token
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Additional authentication data (stored as JSON string if needed)
    auth_data = Column(Text, nullable=True)  # Additional auth info (scopes, etc.)

    # Connection status
    is_active = Column(Boolean, default=True, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship('User', back_populates='platform_connections')
    etsy_stores = relationship('EtsyStore', back_populates='connection')
    shopify_stores = relationship('ShopifyStore', back_populates='connection')

    def is_token_expired(self) -> bool:
        """Check if the access token is expired"""
        if not self.token_expires_at:
            return False
        return datetime.now(timezone.utc) > self.token_expires_at

    def needs_token_refresh(self, threshold_seconds: int = 30) -> bool:
        """Check if the access token needs refreshing (expires within threshold)"""
        if not self.token_expires_at:
            return False
        threshold_time = datetime.now(timezone.utc) + timedelta(seconds=threshold_seconds)
        return self.token_expires_at <= threshold_time

    def time_until_expiry(self) -> timedelta:
        """Get time remaining until token expires"""
        if not self.token_expires_at:
            return timedelta(days=365)  # Return large value if no expiry set
        return self.token_expires_at - datetime.now(timezone.utc)

    def __repr__(self):
        return f"<PlatformConnection(id={self.id}, user_id={self.user_id}, platform={self.platform.value})>"