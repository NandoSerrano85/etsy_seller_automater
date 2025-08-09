from typing import List, Optional
from pydantic import BaseModel

class TopSeller(BaseModel):
    listing_id: int
    title: str
    quantity_sold: int
    total_amount: float
    total_discounts: float
    net_amount: float

class MonthlyBreakdown(BaseModel):
    month: int
    month_name: str
    total_sales: float
    total_quantity: int
    total_discounts: float
    net_sales: float
    receipt_count: int
    top_items: List[TopSeller]

class AnalyticsSummary(BaseModel):
    total_sales: float
    total_quantity: int
    total_discounts: float
    net_sales: float
    total_receipts: int

class MonthlyAnalyticsResponse(BaseModel):
    year: int
    summary: AnalyticsSummary
    monthly_breakdown: List[MonthlyBreakdown]
    year_top_sellers: List[TopSeller]

class ShopListingImage(BaseModel):
    url_full: Optional[str]
    url_75: Optional[str]
    url_170: Optional[str]
    url_570: Optional[str]
    url_640: Optional[str]

class ShopListing(BaseModel):
    listing_id: int
    title: str
    description: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    quantity: Optional[int]
    state: Optional[str]
    images: List[ShopListingImage]
    local_images: List[str]

class ShopListingsResponse(BaseModel):
    designs: List[ShopListing]
    count: int
    total: int
    pagination: dict
    local_images_count: int

class TopSellersResponse(BaseModel):
    year: int
    top_sellers: List[TopSeller]
    total_items: int
