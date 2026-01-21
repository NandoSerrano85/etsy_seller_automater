"""
Storefront Settings Entity

Stores branding, appearance, domain, and configuration settings for the ecommerce storefront.
Supports multi-tenant storefronts with custom domains and subdomains.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class StorefrontSettings(Base):
    """Storefront branding, domain, and appearance settings"""
    __tablename__ = "ecommerce_storefront_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    # Domain Configuration
    subdomain = Column(String(63), unique=True, nullable=True)  # "myshop" → myshop.craftflow.store
    custom_domain = Column(String(255), unique=True, nullable=True)  # "shop.example.com"
    domain_verified = Column(Boolean, default=False)
    domain_verification_token = Column(String(64))
    domain_verification_method = Column(String(20))  # "dns_txt" or "dns_cname"

    # SSL Configuration
    ssl_status = Column(String(20), default='none')  # none, pending, active, failed, expired
    ssl_certificate_path = Column(String(500))
    ssl_private_key_path = Column(String(500))
    ssl_expires_at = Column(DateTime(timezone=True))
    ssl_auto_renew = Column(Boolean, default=True)

    # Store information
    store_name = Column(String(255))
    store_description = Column(Text)

    # Branding assets
    logo_url = Column(String(512))
    favicon_url = Column(String(512))

    # Color scheme
    primary_color = Column(String(7), default="#10b981")  # Hex color code
    secondary_color = Column(String(7), default="#059669")
    accent_color = Column(String(7), default="#34d399")
    text_color = Column(String(7), default="#111827")
    background_color = Column(String(7), default="#ffffff")
    font_family = Column(String(100), default='Inter')

    # Store settings
    currency = Column(String(3), default='USD')
    timezone = Column(String(50), default='America/New_York')
    contact_email = Column(String(255))
    support_phone = Column(String(20))

    # Social Links (JSON)
    social_links = Column(JSONB, default={})  # {"instagram": "...", "facebook": "...", "twitter": "..."}

    # SEO Configuration
    meta_title = Column(String(70))
    meta_description = Column(String(160))
    google_analytics_id = Column(String(20))
    facebook_pixel_id = Column(String(20))

    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)  # Public visibility
    maintenance_mode = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))

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
            "user_id": str(self.user_id) if self.user_id else None,

            # Domain Configuration
            "subdomain": self.subdomain,
            "custom_domain": self.custom_domain,
            "domain_verified": self.domain_verified,
            "domain_verification_token": self.domain_verification_token,
            "domain_verification_method": self.domain_verification_method,

            # SSL Configuration
            "ssl_status": self.ssl_status,
            "ssl_expires_at": self.ssl_expires_at.isoformat() if self.ssl_expires_at else None,
            "ssl_auto_renew": self.ssl_auto_renew,

            # Store information
            "store_name": self.store_name,
            "store_description": self.store_description,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,

            # Color scheme
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "text_color": self.text_color,
            "background_color": self.background_color,
            "font_family": self.font_family,

            # Store settings
            "currency": self.currency,
            "timezone": self.timezone,
            "contact_email": self.contact_email,
            "support_phone": self.support_phone,

            # Social Links
            "social_links": self.social_links or {},

            # SEO Configuration
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "google_analytics_id": self.google_analytics_id,
            "facebook_pixel_id": self.facebook_pixel_id,

            # Status
            "is_active": self.is_active,
            "is_published": self.is_published,
            "maintenance_mode": self.maintenance_mode,
            "published_at": self.published_at.isoformat() if self.published_at else None,

            # Shipping Configuration
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

            # Metadata
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_store_url(self) -> str:
        """Get the public URL for this storefront"""
        if self.custom_domain and self.domain_verified:
            return f"https://{self.custom_domain}"
        elif self.subdomain:
            return f"https://{self.subdomain}.craftflow.store"
        return None

    def get_domain(self) -> str:
        """Get the primary domain for this storefront"""
        if self.custom_domain and self.domain_verified:
            return self.custom_domain
        elif self.subdomain:
            return f"{self.subdomain}.craftflow.store"
        return None
