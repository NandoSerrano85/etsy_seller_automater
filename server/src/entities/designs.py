import os
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Table
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Check if multi-tenant is enabled
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

# Association table for many-to-many relationship between DesignImages and EtsyProductTemplate
design_template_association = Table(
    'design_template_association',
    Base.metadata,
    Column('design_image_id', UUID(as_uuid=True), ForeignKey('design_images.id'), primary_key=True),
    Column('product_template_id', UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), primary_key=True)
)

class DesignImages(Base):
    __tablename__ = 'design_images'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Multi-tenant support - conditionally add org_id
    if MULTI_TENANT_ENABLED:
        org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    description = Column(String, nullable=True)
    phash = Column(String(64), nullable=True)  # Perceptual hash for duplicate detection
    ahash = Column(String(64), nullable=True)  # Perceptual hash for duplicate detection
    dhash = Column(String(64), nullable=True)  # Perceptual hash for duplicate detection
    whash = Column(String(64), nullable=True)  # Perceptual hash for duplicate detection
    tags = Column(JSONB, nullable=True, default=list)  # AI-generated tags for searchability
    tags_metadata = Column(JSONB, nullable=True)  # Metadata about tag generation (model, processing time, categories)
    canvas_config_id = Column(UUID(as_uuid=True), ForeignKey('canvas_configs.id'), nullable=True)
    platform = Column(String(20), default='etsy', nullable=False)  # 'etsy' or 'shopify'
    is_active = Column(Boolean, default=True)
    is_digital = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (temporarily simplified to avoid circular dependencies)
    # organization = relationship('Organization', back_populates='design_images')
    user = relationship('User', back_populates='design_images')
    product_templates = relationship('EtsyProductTemplate', secondary=design_template_association, back_populates='design_images')
    canvas_config = relationship('CanvasConfig', back_populates='design_images')
    size_configs = relationship('SizeConfig', secondary='design_size_config_association', back_populates='design_images')