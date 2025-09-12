"""
Organization models for API requests and responses
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

# Request Models
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    shop_name: str = Field(..., min_length=1, max_length=255, description="Shop name for NAS directory")

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    shop_name: Optional[str] = Field(None, min_length=1, max_length=255)
    billing_customer_id: Optional[str] = None

class OrganizationFeatureUpdate(BaseModel):
    features: Dict[str, bool] = Field(..., description="Feature flags to update")

# Response Models
class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    shop_name: str
    owner_user_id: Optional[UUID] = None
    billing_customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationWithFeaturesResponse(OrganizationResponse):
    features: Dict[str, bool] = {}

class OrganizationStatsResponse(BaseModel):
    id: UUID
    name: str
    shop_name: str
    stats: Dict[str, Any] = {}
    
class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationResponse]
    total: int
    limit: int
    offset: int