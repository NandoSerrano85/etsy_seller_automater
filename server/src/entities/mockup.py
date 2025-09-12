from sqlalchemy import ARRAY, JSON, Column, Float, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class MockupMaskData(Base):
    """This table has the mask data that is associated to the mockup image"""
    __tablename__ = 'mockup_mask_data'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mockup_image_id = Column(UUID(as_uuid=True), ForeignKey('mockup_images.id'), nullable=False)
    masks = Column(JSON, nullable=False)  # Store masks as JSON array
    points = Column(JSON, nullable=False)  # Store points as JSON array
    is_cropped = Column(Boolean, default=False)
    alignment = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    mockup_image = relationship('MockupImage', back_populates='mask_data')

class MockupImage(Base):
    """This table has the mockup image and mask information for the mockups"""
    __tablename__ = 'mockup_images'

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
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)  # Added for multi-tenancy
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=False)
    starting_name = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    organization = relationship('Organization', back_populates='mockups')
    user = relationship('User', back_populates='mockups')
    mockup_images = relationship('MockupImage', back_populates='mockups', cascade='all, delete-orphan')