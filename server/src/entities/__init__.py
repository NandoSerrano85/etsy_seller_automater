"""
Entities package - SQLAlchemy models for the application
"""

import os

# Core entities (always imported)
from .user import User
from .template import EtsyProductTemplate
from .canvas_config import CanvasConfig
from .size_config import SizeConfig
from .designs import DesignImages, design_template_association
from .mockup import Mockups, MockupImage, MockupMaskData
from .third_party_oauth import ThirdPartyOAuthToken

# Multi-tenant entities (conditionally imported)
if os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true':
    from .organization import Organization, OrganizationMember
    from .shop import Shop
else:
    # Define placeholder classes for Organization entities when multi-tenant is disabled
    class Organization:
        pass
    class OrganizationMember:
        pass
    class Shop:
        pass

# Import individual entities that don't have multi-tenant dependencies
from .files import File
from .print_job import PrintJob
from .event import Event
from .org_features import OrgFeatures
from .printer import Printer

# Export all entities
__all__ = [
    'User',
    'EtsyProductTemplate',
    'CanvasConfig', 
    'SizeConfig',
    'DesignImages',
    'design_template_association',
    'Mockups',
    'MockupImage', 
    'MockupMaskData',
    'ThirdPartyOAuthToken',
    'File',
    'PrintJob',
    'Event',
    'OrgFeatures',
    'Printer',
    'Organization',
    'OrganizationMember', 
    'Shop'
]