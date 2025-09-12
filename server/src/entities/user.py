from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TODO: Uncomment after running multi-tenant migration
    # org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)
    
    # User authentication
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='member')  # 'owner', 'admin', 'member'
    
    # Legacy fields (kept for backward compatibility)
    shop_name = Column(String, nullable=True)  # Made nullable as it's now in organization
    etsy_shop_id = Column(String, nullable=True)  # Store Etsy shop ID
    root_folder = Column(String, nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    # TODO: Uncomment after running multi-tenant migration
    # organization = relationship('Organization', back_populates='users')
    third_party_tokens = relationship('ThirdPartyOAuthToken', back_populates='user')
    etsy_product_templates = relationship('EtsyProductTemplate', order_by='EtsyProductTemplate.id', back_populates='user')
    mockups = relationship('Mockups', order_by='Mockups.id', back_populates='user')
    design_images = relationship('DesignImages', order_by='DesignImages.id', back_populates='user')
    # TODO: Uncomment after running multi-tenant migration
    # files = relationship('File', back_populates='created_by_user')
    # print_jobs = relationship('PrintJob', back_populates='created_by_user')
    # events = relationship('Event', back_populates='user')
    # printers = relationship('Printer', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            # TODO: Uncomment after running multi-tenant migration
            # 'org_id': str(self.org_id) if self.org_id else None,
            'email': self.email,
            'role': self.role,
            'shop_name': self.shop_name,
            'etsy_shop_id': self.etsy_shop_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def effective_shop_name(self) -> str:
        """Get shop name from organization or fall back to user's shop_name"""
        # TODO: Uncomment after running multi-tenant migration
        # if self.organization and self.organization.shop_name:
        #     return self.organization.shop_name
        return self.shop_name or 'default'