import os
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID

# Check if multi-tenant is enabled
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenant support - conditionally add org_id
    if MULTI_TENANT_ENABLED:
        org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    
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

    # Subscription plan: 'free', 'basic', 'pro', 'enterprise'
    subscription_plan = Column(String, nullable=False, default='free')

    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships - mix of legacy and multi-tenant
    third_party_tokens = relationship('ThirdPartyOAuthToken', back_populates='user')
    etsy_product_templates = relationship('EtsyProductTemplate', order_by='EtsyProductTemplate.id', back_populates='user')
    shopify_product_templates = relationship('ShopifyProductTemplate', order_by='ShopifyProductTemplate.id', back_populates='user')
    craftflow_commerce_templates = relationship('CraftFlowCommerceTemplate', order_by='CraftFlowCommerceTemplate.id', back_populates='user')
    mockups = relationship('Mockups', order_by='Mockups.id', back_populates='user')
    design_images = relationship('DesignImages', order_by='DesignImages.id', back_populates='user')

    # Platform connections and stores (new architecture)
    platform_connections = relationship('PlatformConnection', back_populates='user')
    etsy_stores = relationship('EtsyStore', back_populates='user')
    shopify_stores = relationship('ShopifyStore', back_populates='user')
    shopify_products = relationship('ShopifyProduct', back_populates='user')
    
    # Multi-tenant relationships - temporarily disabled to resolve join condition issues
    # TODO: Re-enable after Organization relationships are stable
    # if MULTI_TENANT_ENABLED:
    #     organization = relationship('Organization', back_populates='users')
    #     organization_memberships = relationship('OrganizationMember', back_populates='user')
    #     # shops = relationship('Shop', back_populates='user')  # TODO: Enable after shop.py is updated
    #     # files = relationship('File', back_populates='created_by_user')  # TODO: Enable after files.py is updated
    #     # print_jobs = relationship('PrintJob', back_populates='created_by_user')  # TODO: Enable after print_job.py is updated
    #     # events = relationship('Event', back_populates='user')  # TODO: Enable after event.py is updated
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    def to_dict(self):
        result = {
            'id': str(self.id),
            'email': self.email,
            'role': self.role,
            'shop_name': self.shop_name,
            'etsy_shop_id': self.etsy_shop_id,
            'is_active': self.is_active,
            'subscription_plan': self.subscription_plan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Add org_id if multi-tenant is enabled
        if MULTI_TENANT_ENABLED and hasattr(self, 'org_id'):
            result['org_id'] = str(self.org_id) if self.org_id else None
            
        return result
    
    @property
    def effective_shop_name(self) -> str:
        """Get shop name from organization or fall back to user's shop_name"""
        # TODO: Uncomment after running multi-tenant migration
        # if self.organization and self.organization.shop_name:
        #     return self.organization.shop_name
        return self.shop_name or 'default'