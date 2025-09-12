"""
Shop models for API requests and responses
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

# Request Models
class ShopCreate(BaseModel):
    provider: str = Field(default="etsy", description="Shop provider (etsy, shopify, etc.)")
    provider_shop_id: str = Field(..., description="Shop ID from the provider")
    display_name: Optional[str] = Field(None, description="Display name for the shop")
    access_token: Optional[str] = Field(None, description="Access token for API calls")
    refresh_token: Optional[str] = Field(None, description="Refresh token")

class ShopUpdate(BaseModel):
    display_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

# Response Models
class ShopResponse(BaseModel):
    id: UUID
    org_id: UUID
    provider: str
    provider_shop_id: str
    display_name: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ShopListResponse(BaseModel):
    shops: List[ShopResponse]
    total: int
    limit: int
    offset: int