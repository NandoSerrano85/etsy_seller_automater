import os
from sqlalchemy import ARRAY, JSON, Column, Float, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Check if multi-tenant is enabled
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

class MockupMaskData(Base):
    """This table has the mask data that is associated to the mockup image"""
    __tablename__ = 'mockup_mask_data'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mockup_image_id = Column(UUID(as_uuid=True), ForeignKey('mockup_images.id'), nullable=False)
    masks = Column(JSON, nullable=False)  # Store masks as JSON array
    points = Column(JSON, nullable=False)  # Store points as JSON array
    is_cropped = Column(Boolean, default=False)  # Deprecated: Use is_cropped_list for individual mask properties
    alignment = Column(String, nullable=False)  # Deprecated: Use alignment_list for individual mask properties
    # New fields for individual mask properties
    is_cropped_list = Column(JSON, nullable=True)  # List of boolean values for each mask
    alignment_list = Column(JSON, nullable=True)  # List of alignment strings for each mask
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    mockup_image = relationship('MockupImage', back_populates='mask_data')

class MockupImage(Base):
    """This table has the mockup image and mask information for the mockups"""
    __tablename__ = 'mockup_images'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mockups_id = Column(UUID(as_uuid=True), ForeignKey('mockups.id'), nullable=False)
    filename = Column(String, nullable=False)  # Original filename
    file_path = Column(String, nullable=False)  # Path for base mockup image
    watermark_path = Column(String, nullable=True)
    image_type = Column(String, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    mockups = relationship('Mockups', back_populates='mockup_images')
    mask_data = relationship('MockupMaskData', back_populates='mockup_image', cascade='all, delete-orphan')

class Mockups(Base):
    """This table holds the base mockup information."""
    __tablename__ = 'mockups'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Template source and references
    template_source = Column(String, nullable=False, default='etsy')  # etsy, shopify, or craftflow
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=True)  # Etsy template
    shopify_template_id = Column(UUID(as_uuid=True), ForeignKey('shopify_product_templates.id'), nullable=True)  # Shopify template
    craftflow_template_id = Column(UUID(as_uuid=True), ForeignKey('craftflow_commerce_templates.id'), nullable=True)  # CraftFlow template

    # Multi-tenant support - conditionally add org_id
    if MULTI_TENANT_ENABLED:
        org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)
    starting_name = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships (temporarily simplified to avoid circular dependencies)
    # organization = relationship('Organization', back_populates='mockups')
    user = relationship('User', back_populates='mockups')
    mockup_images = relationship('MockupImage', back_populates='mockups', cascade='all, delete-orphan')