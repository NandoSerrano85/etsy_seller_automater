from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Text, Float, Integer
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
    
    # Print quality configuration
    dpi = Column(Integer, nullable=False, default=300)  # DPI for designs using this canvas config
    
    # Gang sheet spacing configuration (in inches)
    spacing_width_inches = Column(Float, nullable=False, default=0.125)  # 1/8 inch default
    spacing_height_inches = Column(Float, nullable=False, default=0.125)  # 1/8 inch default
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product_template = relationship('EtsyProductTemplate', back_populates='canvas_configs')
    size_config = relationship('SizeConfig', back_populates='canvas_config', uselist=False, cascade='all, delete-orphan')
    design_images = relationship('DesignImages', back_populates='canvas_config')
    
    def __repr__(self):
        return f"<CanvasConfig(id={self.id}, name='{self.name}', dpi={self.dpi})>"
    
    @property
    def dimensions_description(self):
        """Human readable dimensions description"""
        return f"{self.width_inches}\" x {self.height_inches}\""
    
    @property
    def spacing_description(self):
        """Human readable spacing description"""
        return f"W: {self.spacing_width_inches}\", H: {self.spacing_height_inches}\""
    
    @classmethod
    def get_dpi_suggestions(cls):
        """Get suggested DPI values for canvas configs"""
        return [150, 200, 300, 400, 500, 600]
    
