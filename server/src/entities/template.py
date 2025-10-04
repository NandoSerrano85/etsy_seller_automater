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


class ShopifyProductTemplate(Base):
    __tablename__ = 'shopify_product_templates'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Multi-tenant support - conditionally add org_id
    if MULTI_TENANT_ENABLED:
        org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)

    # Template metadata
    name = Column(String, nullable=False)  # Internal template name

    # Product details
    template_title = Column(String, nullable=False)  # Product title template (can include {design_name} placeholder)
    description = Column(Text, nullable=True)  # Product description
    vendor = Column(String, nullable=True)  # Product vendor
    product_type = Column(String, nullable=True)  # Product type/category
    tags = Column(Text, nullable=True)  # Comma-separated tags

    # Pricing
    price = Column(Float, nullable=False)  # Base price
    compare_at_price = Column(Float, nullable=True)  # Compare at price (for sales)
    cost_per_item = Column(Float, nullable=True)  # Cost per item

    # Inventory & Shipping
    sku_prefix = Column(String, nullable=True)  # SKU prefix for variants
    barcode_prefix = Column(String, nullable=True)  # Barcode prefix
    track_inventory = Column(Boolean, default=True)  # Track inventory
    inventory_quantity = Column(Integer, default=0)  # Default inventory quantity
    inventory_policy = Column(String, default='deny')  # 'deny' or 'continue' (allow overselling)
    fulfillment_service = Column(String, default='manual')  # 'manual' or fulfillment service
    requires_shipping = Column(Boolean, default=True)  # Requires shipping
    weight = Column(Float, nullable=True)  # Weight in grams
    weight_unit = Column(String, default='g')  # Weight unit (g, kg, oz, lb)

    # Product options/variants
    has_variants = Column(Boolean, default=False)  # Whether product has variants
    option1_name = Column(String, nullable=True)  # First option name (e.g., "Size")
    option1_values = Column(Text, nullable=True)  # Comma-separated values (e.g., "Small,Medium,Large")
    option2_name = Column(String, nullable=True)  # Second option name (e.g., "Color")
    option2_values = Column(Text, nullable=True)  # Comma-separated values
    option3_name = Column(String, nullable=True)  # Third option name
    option3_values = Column(Text, nullable=True)  # Comma-separated values

    # Publishing & SEO
    status = Column(String, default='draft')  # 'active', 'draft', 'archived'
    published_scope = Column(String, default='web')  # 'web', 'global'
    seo_title = Column(String, nullable=True)  # SEO title
    seo_description = Column(Text, nullable=True)  # SEO meta description

    # Tax settings
    is_taxable = Column(Boolean, default=True)  # Is product taxable
    tax_code = Column(String, nullable=True)  # Tax code

    # Additional settings
    gift_card = Column(Boolean, default=False)  # Is this a gift card
    template_suffix = Column(String, nullable=True)  # Theme template suffix

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship('User', back_populates='shopify_product_templates')

    def to_dict(self):
        """Convert template to dictionary"""
        # Get org_id value - will be None if not multi-tenant or not set
        org_id_value = None
        if hasattr(self, 'org_id'):
            org_id_value = str(self.org_id) if self.org_id is not None else None

        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'org_id': org_id_value,
            'name': self.name,
            'template_title': self.template_title,
            'description': self.description,
            'vendor': self.vendor,
            'product_type': self.product_type,
            'tags': self.tags,
            'price': self.price,
            'compare_at_price': self.compare_at_price,
            'cost_per_item': self.cost_per_item,
            'sku_prefix': self.sku_prefix,
            'barcode_prefix': self.barcode_prefix,
            'track_inventory': self.track_inventory,
            'inventory_quantity': self.inventory_quantity,
            'inventory_policy': self.inventory_policy,
            'fulfillment_service': self.fulfillment_service,
            'requires_shipping': self.requires_shipping,
            'weight': self.weight,
            'weight_unit': self.weight_unit,
            'has_variants': self.has_variants,
            'option1_name': self.option1_name,
            'option1_values': self.option1_values,
            'option2_name': self.option2_name,
            'option2_values': self.option2_values,
            'option3_name': self.option3_name,
            'option3_values': self.option3_values,
            'status': self.status,
            'published_scope': self.published_scope,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,
            'is_taxable': self.is_taxable,
            'tax_code': self.tax_code,
            'gift_card': self.gift_card,
            'template_suffix': self.template_suffix,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None,
        }