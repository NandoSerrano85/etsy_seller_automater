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

class ProductVariantConfig(BaseModel):
    option_name: str  # e.g., "Size", "Color"
    option_values: list[str]  # e.g., ["S", "M", "L", "XL"]
    price_modifier: Optional[float] = 0.0  # Additional price per variant

class BulkProductCreateRequest(BaseModel):
    # Name generation settings
    quantity: int
    name_prefix: str
    starting_number: int
    name_postfix: str = ""

    # Standard Shopify product fields
    description: str = ""
    price: float
    vendor: str = "Custom Design Store"
    product_type: str = ""
    tags: str = ""
    status: str = "draft"  # draft, active, archived
    template_suffix: Optional[str] = None  # Theme template suffix

    # Variant settings (optional)
    variants: Optional[list[ProductVariantConfig]] = None

    # Inventory settings
    inventory_quantity: int = 0
    track_inventory: bool = True

    class Config:
        str_strip_whitespace = True

class BulkProductCreateResponse(BaseModel):
    success: bool
    message: str
    products_created: int
    products: list[dict]