from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum

class PlatformTypeEnum(str, Enum):
    """Supported third-party platforms"""
    ETSY = "ETSY"
    SHOPIFY = "SHOPIFY"
    AMAZON = "AMAZON"
    EBAY = "EBAY"

class ConnectionTypeEnum(str, Enum):
    """Types of platform connections"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"

# Base models for platform connections
class PlatformConnectionBase(BaseModel):
    platform: PlatformTypeEnum
    connection_type: ConnectionTypeEnum = ConnectionTypeEnum.OAUTH2
    is_active: bool = True

class PlatformConnectionCreate(PlatformConnectionBase):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    auth_data: Optional[str] = None

class PlatformConnectionUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    auth_data: Optional[str] = None
    is_active: Optional[bool] = None

class PlatformConnectionResponse(PlatformConnectionBase):
    id: UUID
    user_id: UUID
    last_verified_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    is_token_expired: bool = Field(description="True if the access token is expired")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlatformConnectionListResponse(BaseModel):
    connections: List[PlatformConnectionResponse]
    total: int

# Base models for Etsy stores
class EtsyStoreBase(BaseModel):
    shop_name: str
    etsy_shop_id: str
    shop_url: Optional[str] = None
    currency_code: Optional[str] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    is_active: bool = True
    is_vacation_mode: bool = False

class EtsyStoreCreate(EtsyStoreBase):
    connection_id: UUID

class EtsyStoreUpdate(BaseModel):
    shop_name: Optional[str] = None
    shop_url: Optional[str] = None
    currency_code: Optional[str] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None
    is_vacation_mode: Optional[bool] = None
    total_listings: Optional[int] = None
    total_sales: Optional[int] = None

class EtsyStoreResponse(EtsyStoreBase):
    id: UUID
    user_id: UUID
    connection_id: UUID
    total_listings: Optional[int] = None
    total_sales: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EtsyStoreListResponse(BaseModel):
    stores: List[EtsyStoreResponse]
    total: int

# Enhanced Shopify store models (updating existing structure)
class ShopifyStoreEnhancedBase(BaseModel):
    shop_domain: str
    shop_name: str
    shopify_shop_id: Optional[str] = None
    shop_url: Optional[str] = None
    currency_code: Optional[str] = None
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    is_active: bool = True

class ShopifyStoreEnhancedCreate(ShopifyStoreEnhancedBase):
    connection_id: UUID

class ShopifyStoreEnhancedUpdate(BaseModel):
    shop_name: Optional[str] = None
    shopify_shop_id: Optional[str] = None
    shop_url: Optional[str] = None
    currency_code: Optional[str] = None
    country_code: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    total_products: Optional[int] = None
    total_orders: Optional[int] = None

class ShopifyStoreEnhancedResponse(ShopifyStoreEnhancedBase):
    id: UUID
    user_id: UUID
    connection_id: Optional[UUID] = None  # Nullable during migration
    total_products: Optional[int] = None
    total_orders: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShopifyStoreEnhancedListResponse(BaseModel):
    stores: List[ShopifyStoreEnhancedResponse]
    total: int

# Combined platform setup models
class PlatformSetupRequest(BaseModel):
    """Request to setup a new platform connection with store"""
    platform: PlatformTypeEnum
    connection_data: PlatformConnectionCreate
    store_data: dict  # Platform-specific store data

class PlatformSetupResponse(BaseModel):
    """Response after setting up platform connection"""
    success: bool
    message: str
    connection: Optional[PlatformConnectionResponse] = None
    store_id: Optional[UUID] = None

# Connection verification models
class ConnectionVerificationResponse(BaseModel):
    is_valid: bool
    platform: PlatformTypeEnum
    last_verified_at: Optional[datetime] = None
    error_message: Optional[str] = None

class BulkConnectionVerificationResponse(BaseModel):
    connections: List[ConnectionVerificationResponse]
    total_checked: int
    valid_connections: int