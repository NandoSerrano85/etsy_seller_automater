"""
Entities package - SQLAlchemy models for the application
"""

# Import all entities to ensure they are registered with SQLAlchemy
from .organization import Organization, OrganizationMember
from .user import User
from .shop import Shop
from .files import File
from .template import EtsyProductTemplate
from .canvas_config import CanvasConfig
from .size_config import SizeConfig
from .designs import DesignImages, design_template_association
from .mockup import Mockups, MockupImage, MockupMaskData
from .third_party_oauth import ThirdPartyOAuthToken
from .print_job import PrintJob
from .event import Event
from .org_features import OrgFeatures
from .printer import Printer

# Export all entities
__all__ = [
    'Organization',
    'OrganizationMember',
    'User',
    'Shop',
    'File',
    'EtsyProductTemplate',
    'CanvasConfig',
    'SizeConfig',
    'DesignImages',
    'design_template_association',
    'Mockups',
    'MockupImage',
    'MockupMaskData',
    'ThirdPartyOAuthToken',
    'PrintJob',
    'Event',
    'OrgFeatures',
    'Printer'
]