from sqlalchemy import Column, DateTime, func, ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class ShopifyStore(Base):
    """
    Stores Shopify shop/store business information.
    Authentication credentials moved to PlatformConnection entity.
    """
    __tablename__ = 'shopify_stores'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey('platform_connections.id'), nullable=True)  # Nullable for migration

    # Shopify store identification
    shopify_shop_id = Column(String(50), nullable=True)  # Shopify's internal shop ID
    shop_domain = Column(String(255), nullable=False)  # shop.myshopify.com
    shop_name = Column(String(255), nullable=False)  # Display name of the shop

    # Store information
    shop_url = Column(String(255), nullable=True)  # Custom domain if any
    currency_code = Column(String(3), nullable=True)  # ISO currency code
    country_code = Column(String(2), nullable=True)  # ISO country code
    timezone = Column(String(50), nullable=True)  # Shop timezone

    # Legacy field (for backward compatibility during migration)
    access_token = Column(String, nullable=True)  # Will be moved to PlatformConnection

    # Store status
    is_active = Column(Boolean, default=True, nullable=False)

    # Store metrics (optional)
    total_products = Column(Integer, nullable=True)
    total_orders = Column(Integer, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship('User', back_populates='shopify_stores')
    connection = relationship('PlatformConnection', back_populates='shopify_stores')
    products = relationship('ShopifyProduct', back_populates='store')

    def __repr__(self):
        return f"<ShopifyStore(id={self.id}, shop_name={self.shop_name}, shop_domain={self.shop_domain})>"