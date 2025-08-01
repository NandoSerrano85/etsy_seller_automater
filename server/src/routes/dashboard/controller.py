from fastapi import APIRouter, Depends, Query
from server.src.routes.auth.service import CurrentUser
from . import model
from . import service

router = APIRouter(
    prefix='/dashboard',
    tags=['Dashboard']
)

@router.get('/analytics', response_model=model.MonthlyAnalyticsResponse)
async def get_monthly_analytics(
    current_user: CurrentUser,
    access_token: str = Query(..., description="Etsy access token"),
    year: int = Query(None, description="Year for analytics")
):
    return service.get_monthly_analytics(access_token, year, current_user)

@router.get('/top-sellers', response_model=model.TopSellersResponse)
async def get_top_sellers(
    current_user: CurrentUser,
    access_token: str = Query(..., description="Etsy access token"),
    year: int = Query(None, description="Year for top sellers")
):
    return service.get_top_sellers(access_token, year, current_user)

@router.get('/shop-listings', response_model=model.ShopListingsResponse)
async def get_shop_listings(
    current_user: CurrentUser,
    access_token: str = Query(..., description="Etsy access token"),
    limit: int = Query(50, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    return service.get_shop_listings(access_token, limit, offset, current_user)
