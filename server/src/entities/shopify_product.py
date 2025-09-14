from sqlalchemy import Column, DateTime, func, ForeignKey, Text, String, Float, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class ShopifyProduct(Base):
    __tablename__ = 'shopify_products'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('shopify_stores.id'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=True)

    # Shopify product information
    shopify_product_id = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    handle = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    vendor = Column(String, nullable=True)
    product_type = Column(String, nullable=True)
    tags = Column(Text, nullable=True)

    # Product variants (stored as JSON)
    variants = Column(JSON, nullable=True)

    # Design information
    design_files = Column(JSON, nullable=True)  # Store design file paths/URLs
    mockup_images = Column(JSON, nullable=True)  # Store generated mockup image paths

    # Publishing status
    published_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default='draft')  # draft, active, archived

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship('User', back_populates='shopify_products')
    store = relationship('ShopifyStore', back_populates='products')
    template = relationship('EtsyProductTemplate', back_populates='shopify_products')

# Add the relationship to ShopifyStore
from server.src.entities.shopify_store import ShopifyStore
from server.src.entities.template import EtsyProductTemplate
from server.src.entities.user import User

# Note: These relationships will be added via migrations or direct model updates