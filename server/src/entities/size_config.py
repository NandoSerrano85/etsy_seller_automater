from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Text, Float, Table
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Association table for many-to-many relationship between DesignImages and SizeConfig
design_size_config_association = Table(
    'design_size_config_association',
    Base.metadata,
    Column('design_image_id', UUID(as_uuid=True), ForeignKey('design_images.id'), primary_key=True),
    Column('size_config_id', UUID(as_uuid=True), ForeignKey('size_configs.id'), primary_key=True)
)

class SizeConfig(Base):
    __tablename__ = 'size_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=False)
    canvas_id = Column(UUID(as_uuid=True), ForeignKey('canvas_configs.id'), nullable=False)
    name = Column(String, nullable=False)  # e.g., 'Adult+', 'Adult', 'Youth', 'Toddler', 'Pocket'
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product_template = relationship('EtsyProductTemplate', back_populates='size_configs')
    canvas_config = relationship('CanvasConfig', back_populates='size_config', uselist=False)
    design_images = relationship('DesignImages', secondary=design_size_config_association, back_populates='size_configs')