"""
Storefront Settings Entity

Stores branding and appearance settings for the ecommerce storefront.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class StorefrontSettings(Base):
    """Storefront branding and appearance settings"""
    __tablename__ = "ecommerce_storefront_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

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

    # Shipping Configuration (Origin/Warehouse Address)
    shipping_from_name = Column(String(255))
    shipping_from_company = Column(String(255))
    shipping_from_street1 = Column(String(255))
    shipping_from_street2 = Column(String(255))
    shipping_from_city = Column(String(100))
    shipping_from_state = Column(String(50))
    shipping_from_zip = Column(String(20))
    shipping_from_country = Column(String(50), default="US")
    shipping_from_phone = Column(String(50))
    shipping_from_email = Column(String(255))

    # Default Package Dimensions
    shipping_default_length = Column(String(10), default="10")  # inches
    shipping_default_width = Column(String(10), default="8")
    shipping_default_height = Column(String(10), default="4")
    shipping_default_weight = Column(String(10), default="1")  # pounds

    # Shippo API Configuration
    shippo_api_key = Column(String(255))
    shippo_test_mode = Column(String(10), default="true")

    # Shipping Pricing
    handling_fee = Column(String(10), default="0.00")  # Additional handling fee added to shipping cost

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
            "shipping_from_name": self.shipping_from_name,
            "shipping_from_company": self.shipping_from_company,
            "shipping_from_street1": self.shipping_from_street1,
            "shipping_from_street2": self.shipping_from_street2,
            "shipping_from_city": self.shipping_from_city,
            "shipping_from_state": self.shipping_from_state,
            "shipping_from_zip": self.shipping_from_zip,
            "shipping_from_country": self.shipping_from_country,
            "shipping_from_phone": self.shipping_from_phone,
            "shipping_from_email": self.shipping_from_email,
            "shipping_default_length": self.shipping_default_length,
            "shipping_default_width": self.shipping_default_width,
            "shipping_default_height": self.shipping_default_height,
            "shipping_default_weight": self.shipping_default_weight,
            "shippo_api_key": self.shippo_api_key,
            "shippo_test_mode": self.shippo_test_mode,
            "handling_fee": self.handling_fee,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
