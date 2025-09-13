"""
Organization Entity for Multi-tenant Architecture
"""

import os
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from ..database.core import Base

# Only define multi-tenant entities if enabled or migration is in progress
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

class Organization(Base):
    __tablename__ = 'organizations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    settings = Column(JSONB, default={})
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Conditional relationships - only active if multi-tenant is enabled
    if MULTI_TENANT_ENABLED:
        users = relationship("User", back_populates="organization")
        members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
        shops = relationship("Shop", back_populates="organization", cascade="all, delete-orphan")
        printers = relationship("Printer", back_populates="organization", cascade="all, delete-orphan")
        # files = relationship("File", back_populates="organization", cascade="all, delete-orphan")
        # print_jobs = relationship("PrintJob", back_populates="organization", cascade="all, delete-orphan")  
        # events = relationship("Event", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OrganizationMember(Base):
    __tablename__ = 'organization_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(50), default='member')  # 'owner', 'admin', 'member'
    
    # Audit fields
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Conditional relationships
    if MULTI_TENANT_ENABLED:
        organization = relationship("Organization", back_populates="members")
        user = relationship("User", back_populates="organization_memberships")
    
    def __repr__(self):
        return f"<OrganizationMember(org_id={self.organization_id}, user_id={self.user_id}, role={self.role})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'user_id': str(self.user_id),
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }


# Other multi-tenant entities are defined in their respective files:
# - Shop: shop.py
# - Printer: printer.py  
# - File: files.py
# - PrintJob: print_job.py
# - Event: event.py