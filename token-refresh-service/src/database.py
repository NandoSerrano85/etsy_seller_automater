"""Database connection and models for token refresh service."""
import os
import logging
import enum
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PlatformType(enum.Enum):
    """Supported third-party platforms"""
    ETSY = "ETSY"
    SHOPIFY = "SHOPIFY"
    AMAZON = "AMAZON"
    EBAY = "EBAY"


class ConnectionType(enum.Enum):
    """Types of platform connections"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"


class PlatformConnection(Base):
    """Platform connection model - matches server entity."""
    __tablename__ = "platform_connections"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    connection_type = Column(Enum(ConnectionType), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ShopifyStore(Base):
    """Shopify store model - matches server entity (legacy support)."""
    __tablename__ = "shopify_stores"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    connection_id = Column(UUID(as_uuid=True), nullable=True)
    shop_domain = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    access_token = Column(String, nullable=True)  # Legacy field
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Error creating database session: {e}")
        raise
