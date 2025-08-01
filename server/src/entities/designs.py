from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Table
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Association table for many-to-many relationship between DesignImages and EtsyProductTemplate
design_template_association = Table(
    'design_template_association',
    Base.metadata,
    Column('design_image_id', UUID(as_uuid=True), ForeignKey('design_images.id'), primary_key=True),
    Column('product_template_id', UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), primary_key=True)
)

class DesignImages(Base):
    __tablename__ = 'design_images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    description = Column(String, nullable=True)
    canvas_config_id = Column(UUID(as_uuid=True), ForeignKey('canvas_configs.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship('User', back_populates='design_images')
    product_templates = relationship('EtsyProductTemplate', secondary=design_template_association, back_populates='design_images')
    canvas_config = relationship('CanvasConfig', back_populates='design_images')
    size_configs = relationship('SizeConfig', secondary='design_size_config_association', back_populates='design_images')