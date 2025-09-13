"""
Organization Features Entity for Feature Flags
"""

import os
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database.core import Base

# Check if multi-tenant is enabled
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

# Only define OrgFeatures if multi-tenant is enabled
if MULTI_TENANT_ENABLED:
    class OrgFeatures(Base):
        __tablename__ = 'org_features'
        
        org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True)
        features = Column(JSONB, default={
            "mockups": True,
            "print": True,
            "designs": True,
            "orders": True,
            "analytics": True
        })
        
        # Relationships (temporarily simplified to avoid circular dependencies)
        # organization = relationship("Organization", backref="features")
        
        def __repr__(self):
            return f"<OrgFeatures(org_id={self.org_id}, features={self.features})>"
        
        def has_feature(self, feature_name: str) -> bool:
            """Check if organization has a specific feature enabled"""
            return self.features.get(feature_name, False)
        
        def enable_feature(self, feature_name: str):
            """Enable a feature for the organization"""
            if self.features is None:
                self.features = {}
            self.features[feature_name] = True
        
        def disable_feature(self, feature_name: str):
            """Disable a feature for the organization"""
            if self.features is None:
                self.features = {}
            self.features[feature_name] = False
        
        def to_dict(self):
            return {
                'org_id': str(self.org_id),
                'features': self.features or {}
            }
else:
    # Placeholder class when multi-tenant is disabled
    class OrgFeatures:
        pass

# Feature constants
class Features:
    MOCKUPS = "mockups"
    PRINT = "print"
    DESIGNS = "designs"
    ORDERS = "orders"
    ANALYTICS = "analytics"
    MULTI_USER = "multi_user"
    API_ACCESS = "api_access"