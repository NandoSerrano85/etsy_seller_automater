"""
Storefront Settings Entity

Stores branding and appearance settings for the ecommerce storefront.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class StorefrontSettings(Base):
    """Storefront branding and appearance settings"""
    __tablename__ = "ecommerce_storefront_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True)

    # Store information
    store_name = Column(String(255))
    store_description = Column(Text)

    # Branding assets
    logo_url = Column(String(512))

    # Color scheme
    primary_color = Column(String(7), default="#10b981")  # Hex color code
    secondary_color = Column(String(7), default="#059669")
    accent_color = Column(String(7), default="#34d399")
    text_color = Column(String(7), default="#111827")
    background_color = Column(String(7), default="#ffffff")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "store_name": self.store_name,
            "store_description": self.store_description,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "text_color": self.text_color,
            "background_color": self.background_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
