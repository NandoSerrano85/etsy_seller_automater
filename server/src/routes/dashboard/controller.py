from fastapi import APIRouter, Depends, Query, HTTPException, status
from server.src.routes.auth.service import CurrentUser, CurrentShopInfo
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.entities.third_party_oauth import ThirdPartyOAuthToken
from server.src.services.cache_service import ApiCache
from datetime import datetime, timezone
from . import model
from . import service
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix='/dashboard',
    tags=['Dashboard']
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="dashboard-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

def get_user_etsy_token(current_user: CurrentUser, db: Session) -> str:
    """Get user's Etsy access token from database."""
    oauth_record = db.query(ThirdPartyOAuthToken).filter(
        ThirdPartyOAuthToken.user_id == current_user.get_uuid()
    ).first()
    
    if not oauth_record or not oauth_record.access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Etsy connection found. Please connect your Etsy account first."
        )
    
    # Check if token is expired
    if oauth_record.expires_at and oauth_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Etsy access token has expired. Please reconnect your Etsy account."
        )
    
    return oauth_record.access_token

@router.get('/analytics', response_model=model.MonthlyAnalyticsResponse)
async def get_monthly_analytics(
    current_user: CurrentUser,
    shop_info: CurrentShopInfo,
    year: int = Query(None, description="Year for analytics"),
    db: Session = Depends(get_db)
):
    if not shop_info.has_shop_id():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Etsy shop ID found. Please reconnect your Etsy account."
        )

    # Use current year if not provided
    if year is None:
        year = datetime.now().year

    user_id = str(current_user.get_uuid())

    # Try to get from cache first (1 hour TTL)
    cached_result = await ApiCache.get_analytics_cache(user_id, year)
    if cached_result is not None:
        return cached_result

    # Get fresh data in thread
    @run_in_thread
    def get_monthly_analytics_threaded():
        access_token = get_user_etsy_token(current_user, db)
        return service.get_monthly_analytics(access_token, year, shop_info.shop_id)

    result = await get_monthly_analytics_threaded()

    # Cache the result for 1 hour
    await ApiCache.set_analytics_cache(user_id, year, result, 3600)

    return result

@router.get('/top-sellers', response_model=model.TopSellersResponse)
async def get_top_sellers(
    current_user: CurrentUser,
    shop_info: CurrentShopInfo,
    year: int = Query(None, description="Year for top sellers"),
    db: Session = Depends(get_db)
):
    """Get top sellers (threaded)"""
    if not shop_info.has_shop_id():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Etsy shop ID found. Please reconnect your Etsy account."
        )

    @run_in_thread
    def get_top_sellers_threaded():
        access_token = get_user_etsy_token(current_user, db)
        return service.get_top_sellers(access_token, year, shop_info.shop_id)

    return await get_top_sellers_threaded()

@router.get('/shop-listings', response_model=model.ShopListingsResponse)
async def get_shop_listings(
    current_user: CurrentUser,
    shop_info: CurrentShopInfo,
    limit: int = Query(50, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get shop listings (threaded)"""
    if not shop_info.has_shop_id():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Etsy shop ID found. Please reconnect your Etsy account."
        )

    @run_in_thread
    def get_shop_listings_threaded():
        access_token = get_user_etsy_token(current_user, db)
        return service.get_shop_listings(access_token, limit, offset, shop_info.shop_id)

    return await get_shop_listings_threaded()
