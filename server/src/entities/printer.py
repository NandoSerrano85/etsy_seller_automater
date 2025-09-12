"""
Printer entity for user-specific printer configurations
"""

import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.src.database.core import Base

class PrinterType(enum.Enum):
    """Types of printers supported"""
    INKJET = "inkjet"
    LASER = "laser"
    SUBLIMATION = "sublimation"
    DTG = "dtg"  # Direct to Garment
    VINYL = "vinyl"
    UV = "uv"
    OTHER = "other"

class Printer(Base):
    """
    Printer configuration entity
    Each user can have multiple printers with different capabilities
    """
    __tablename__ = 'printers'
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Printer information
    name = Column(String(255), nullable=False, index=True)
    printer_type = Column(String(50), nullable=False, default=PrinterType.INKJET.value)
    manufacturer = Column(String(100))
    model = Column(String(100))
    description = Column(Text)
    
    # Print area dimensions (in inches)
    max_width_inches = Column(Float, nullable=False)
    max_height_inches = Column(Float, nullable=False)
    
    # Print quality settings
    dpi = Column(Integer, nullable=False, default=300)
    
    # Supported templates (array of template IDs this printer can handle)
    supported_template_ids = Column(ARRAY(UUID), default=lambda: [])
    
    # Printer status and settings
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)  # Default printer for user
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="printers")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<Printer(id={self.id}, name='{self.name}', type='{self.printer_type}', dpi={self.dpi})>"
    
    @property
    def print_area_description(self):
        """Human readable print area description"""
        return f"{self.max_width_inches}\" x {self.max_height_inches}\""
    
    @property
    def is_large_format(self):
        """Check if this is a large format printer (> 13 inches in any dimension)"""
        return self.max_width_inches > 13 or self.max_height_inches > 13
    
    def can_print_size(self, width_inches: float, height_inches: float) -> bool:
        """Check if printer can handle the given dimensions"""
        return (width_inches <= self.max_width_inches and 
                height_inches <= self.max_height_inches)
    
    def supports_template(self, template_id: str) -> bool:
        """Check if printer supports a specific template"""
        if not self.supported_template_ids:
            return False
        return str(template_id) in [str(tid) for tid in self.supported_template_ids]
    
    @classmethod
    def get_dpi_suggestions(cls):
        """Get suggested DPI values"""
        return [300, 400, 500, 600]
    
    @classmethod
    def get_printer_types(cls):
        """Get available printer types"""
        return [ptype.value for ptype in PrinterType]