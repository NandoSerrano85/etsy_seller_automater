from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ListingImage(BaseModel):
    """Model for listing image data"""
    listing_image_id: int
    hex_code: Optional[str] = None
    red: Optional[int] = None
    green: Optional[int] = None
    blue: Optional[int] = None
    hue: Optional[int] = None
    saturation: Optional[int] = None
    brightness: Optional[int] = None
    is_black_and_white: Optional[bool] = None
    creation_tsz: Optional[int] = None
    created_timestamp: Optional[int] = None
    rank: Optional[int] = None
    url_75x75: Optional[str] = None
    url_170x135: Optional[str] = None
    url_570xN: Optional[str] = None
    url_fullxfull: Optional[str] = None
    full_height: Optional[int] = None
    full_width: Optional[int] = None
    alt_text: Optional[str] = None


class ListingResponse(BaseModel):
    """Response model for individual listing data"""
    listing_id: int
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    state: Optional[str] = None
    tags: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    taxonomy_id: Optional[int] = None
    shop_section_id: Optional[int] = None
    shipping_profile_id: Optional[int] = None
    item_weight: Optional[float] = None
    item_weight_unit: Optional[str] = None
    item_length: Optional[float] = None
    item_width: Optional[float] = None
    item_height: Optional[float] = None
    item_dimensions_unit: Optional[str] = None
    return_policy_id: Optional[int] = None
    who_made: Optional[str] = None
    when_made: Optional[str] = None
    is_taxable: Optional[bool] = None
    processing_min: Optional[int] = None
    processing_max: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Image fields
    images: Optional[List[ListingImage]] = None
    default_image_url: Optional[str] = None  # URL of the primary/first image


class ListingsResponse(BaseModel):
    """Response model for bulk listings data"""
    listings: List[ListingResponse]
    count: int
    total: int
    success_code: int = 200
    message: Optional[str] = "Listings retrieved successfully"


class ListingUpdateRequest(BaseModel):
    """Request model for updating a single listing"""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    tags: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    taxonomy_id: Optional[int] = None
    shop_section_id: Optional[int] = None
    shipping_profile_id: Optional[int] = None
    item_weight: Optional[float] = None
    item_weight_unit: Optional[str] = None
    item_length: Optional[float] = None
    item_width: Optional[float] = None
    item_height: Optional[float] = None
    item_dimensions_unit: Optional[str] = None
    return_policy_id: Optional[int] = None
    who_made: Optional[str] = None
    when_made: Optional[str] = None
    is_taxable: Optional[bool] = None
    processing_min: Optional[int] = None
    processing_max: Optional[int] = None


class BulkListingUpdateRequest(BaseModel):
    """Request model for bulk updating listings"""
    listing_ids: List[int] = Field(..., description="List of listing IDs to update")
    updates: ListingUpdateRequest = Field(..., description="Updates to apply to all selected listings")


class SelectedListingsUpdateRequest(BaseModel):
    """Request model for updating specific listings with individual data"""
    listing_updates: List[Dict[str, Any]] = Field(..., description="List of listing updates, each must contain 'listing_id' and update fields")


class ListingUpdateResult(BaseModel):
    """Result model for individual listing update"""
    listing_id: int
    success: bool
    data: Optional[ListingResponse] = None
    error: Optional[str] = None


class BulkUpdateResponse(BaseModel):
    """Response model for bulk update operations"""
    successful: List[ListingUpdateResult]
    failed: List[ListingUpdateResult]
    total: int
    success_count: int
    failure_count: int
    success_code: int = 200
    message: Optional[str] = "Bulk update completed"


class GetListingsRequest(BaseModel):
    """Request model for getting listings with filters"""
    state: str = Field(default="active", description="Filter by listing state (active, draft, expired, etc.)")
    limit: Optional[int] = Field(default=100, le=100, description="Number of listings to return (max 100)")
    offset: Optional[int] = Field(default=0, description="Number of listings to skip for pagination")


class GetAllListingsRequest(BaseModel):
    """Request model for getting all listings"""
    state: str = Field(default="active", description="Filter by listing state (active, draft, expired, etc.)")


class DropdownOption(BaseModel):
    """Model for dropdown options"""
    id: int
    name: str


class TaxonomiesResponse(BaseModel):
    """Response model for taxonomies (categories)"""
    taxonomies: List[DropdownOption]
    success_code: int = 200
    message: Optional[str] = "Taxonomies retrieved successfully"


class ShippingProfilesResponse(BaseModel):
    """Response model for shipping profiles"""
    shipping_profiles: List[DropdownOption]
    success_code: int = 200
    message: Optional[str] = "Shipping profiles retrieved successfully"


class ShopSectionsResponse(BaseModel):
    """Response model for shop sections"""
    shop_sections: List[DropdownOption]
    success_code: int = 200
    message: Optional[str] = "Shop sections retrieved successfully"