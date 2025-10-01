import os
from sqlalchemy import Column, Float, Integer, String, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID

# Check if multi-tenant is enabled
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

class EtsyProductTemplate(Base):
    __tablename__ = 'etsy_product_templates'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Multi-tenant support - conditionally add org_id
    if MULTI_TENANT_ENABLED:
        org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)
    name = Column(String, nullable=False)  # e.g., 'UVDTF 16oz'
    template_title = Column(String, nullable=True)  # User-friendly template name/key
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    who_made = Column(String, nullable=True)
    when_made = Column(String, nullable=True)
    taxonomy_id = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    materials = Column(Text, nullable=True)  # Store as comma-separated or JSON string
    shop_section_id = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)  # Store as comma-separated or JSON string
    item_weight = Column(Float, nullable=True)
    item_weight_unit = Column(String, nullable=True)
    item_length = Column(Float, nullable=True)
    item_width = Column(Float, nullable=True)
    item_height = Column(Float, nullable=True)
    item_dimensions_unit = Column(String, nullable=True)
    is_taxable = Column(Boolean, nullable=True)
    type = Column(String, nullable=True)
    processing_min = Column(Integer, nullable=True)
    processing_max = Column(Integer, nullable=True)
    return_policy_id = Column(Integer, nullable=True)
    production_partner_ids = Column(Text, nullable=True)  # Comma-separated list of production partner IDs (required for physical items)
    readiness_state_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships
    # Temporarily commented out to avoid circular dependencies
    # organization = relationship('Organization', back_populates='templates')
    user = relationship('User', back_populates='etsy_product_templates')
    canvas_configs = relationship('CanvasConfig', back_populates='product_template')
    size_configs = relationship('SizeConfig', back_populates='product_template')
    design_images = relationship('DesignImages', secondary='design_template_association', back_populates='product_templates')
    shopify_products = relationship('ShopifyProduct', back_populates='template')