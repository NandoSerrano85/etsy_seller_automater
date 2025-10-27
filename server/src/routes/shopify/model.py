from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ShopifyOAuthInitRequest(BaseModel):
    shop_domain: str

    class Config:
        str_strip_whitespace = True

class ShopifyOAuthInitResponse(BaseModel):
    authorization_url: str
    state: str

class ShopifyStoreResponse(BaseModel):
    id: UUID
    user_id: UUID
    shop_domain: str
    shop_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShopifyOAuthCallbackResponse(BaseModel):
    success: bool
    message: str
    store: Optional[ShopifyStoreResponse] = None

class ShopifyStoresListResponse(BaseModel):
    stores: list[ShopifyStoreResponse]
    total: int

class ShopifyPrintFilesFromSelectionRequest(BaseModel):
    order_ids: list[int]  # Shopify order IDs
    template_name: str

class PrintFilesResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    sheets_created: Optional[int] = None