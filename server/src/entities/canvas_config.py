from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class CanvasConfig(Base):
    __tablename__ = 'canvas_configs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=False)
    name = Column(String, nullable=False)  # e.g., 'UVDTF Decal'
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_stretch = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product_template = relationship('EtsyProductTemplate', back_populates='canvas_configs')
    size_config = relationship('SizeConfig', back_populates='canvas_config', uselist=False, cascade='all, delete-orphan')
    design_images = relationship('DesignImages', back_populates='canvas_config')
