"""
Organization Entity for Multi-tenant Architecture
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from ..database.core import Base

class Organization(Base):
    __tablename__ = 'organizations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    shop_name = Column(String(255), nullable=False)  # Maps to NAS directory
    owner_user_id = Column(UUID(as_uuid=True))  # Will be linked after User entity update
    billing_customer_id = Column(String(255))  # For Stripe integration
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships (will be defined after other entities are created)
    users = relationship("User", back_populates="organization")
    shops = relationship("Shop", back_populates="organization")
    files = relationship("File", back_populates="organization")
    design_images = relationship("DesignImages", back_populates="organization")
    templates = relationship("EtsyProductTemplate", back_populates="organization")
    mockups = relationship("Mockups", back_populates="organization")
    print_jobs = relationship("PrintJob", back_populates="organization")
    events = relationship("Event", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, shop_name={self.shop_name})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'shop_name': self.shop_name,
            'owner_user_id': str(self.owner_user_id) if self.owner_user_id else None,
            'billing_customer_id': self.billing_customer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }