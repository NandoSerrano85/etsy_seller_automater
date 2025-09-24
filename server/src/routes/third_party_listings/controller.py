from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.entities.user import User
from . import service, model
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(prefix="/third-party-listings", tags=["third-party-listings"])

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="third-party-listings-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper


@router.get("/", response_model=model.ListingsResponse)
async def get_shop_listings(
    current_user: CurrentUser,
    state: str = Query(default="active", description="Filter by listing state (active, draft, expired, etc.)"),
    limit: Optional[int] = Query(default=100, le=100, description="Number of listings to return (max 100)"),
    offset: Optional[int] = Query(default=0, description="Number of listings to skip for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get shop listings with pagination and filtering (threaded)
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    request = model.GetListingsRequest(
        state=state,
        limit=limit,
        offset=offset
    )

    @run_in_thread
    def get_shop_listings_threaded():
        return service.get_shop_listings(user_id, db, request)

    return await get_shop_listings_threaded()


@router.get("/all", response_model=model.ListingsResponse)
async def get_all_shop_listings(
    current_user: CurrentUser,
    state: str = Query(default="active", description="Filter by listing state (active, draft, expired, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Get all shop listings (with automatic pagination) (threaded)
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    request = model.GetAllListingsRequest(state=state)

    @run_in_thread
    def get_all_shop_listings_threaded():
        return service.get_all_shop_listings(user_id, db, request)

    return await get_all_shop_listings_threaded()


@router.get("/{listing_id}", response_model=model.ListingResponse)
async def get_listing_by_id(
    listing_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Get a specific listing by ID (threaded)
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_listing_by_id_threaded():
        return service.get_listing_by_id(user_id, db, listing_id)

    return await get_listing_by_id_threaded()


@router.patch("/{listing_id}", response_model=model.ListingResponse)
async def update_listing(
    listing_id: int,
    update_request: model.ListingUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update a specific listing
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return service.update_listing(user_id, db, listing_id, update_request)


@router.post("/bulk-update", response_model=model.BulkUpdateResponse)
async def bulk_update_listings(
    request: model.BulkListingUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update multiple listings with the same data
    
    This endpoint allows you to update multiple listings at once with the same field values.
    For example, you can update the price, description, or tags for multiple listings simultaneously.
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return service.bulk_update_listings(user_id, db, request)


@router.post("/selected-update", response_model=model.BulkUpdateResponse)
async def update_selected_listings(
    request: model.SelectedListingsUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update specific listings with individual update data
    
    This endpoint allows you to update multiple listings with different field values for each listing.
    Each listing update should contain 'listing_id' and the specific fields to update for that listing.
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return service.update_selected_listings(user_id, db, request)


@router.get("/options/taxonomies", response_model=model.TaxonomiesResponse)
async def get_taxonomies(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Get all available taxonomies (categories) for listings
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return service.get_taxonomies(user_id, db)


@router.get("/options/shipping-profiles", response_model=model.ShippingProfilesResponse)
async def get_shipping_profiles(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Get all available shipping profiles
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return service.get_shipping_profiles(user_id, db)


@router.get("/options/shop-sections", response_model=model.ShopSectionsResponse)
async def get_shop_sections(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Get all available shop sections
    """
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return service.get_shop_sections(user_id, db)