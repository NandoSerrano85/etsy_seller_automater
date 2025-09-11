from fastapi import APIRouter, Depends, Query, HTTPException, status
from server.src.routes.auth.service import CurrentUser
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.entities.third_party_oauth import ThirdPartyOAuthToken
from datetime import datetime, timezone
from . import model
from . import service

router = APIRouter(
    prefix='/dashboard',
    tags=['Dashboard']
)

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
    year: int = Query(None, description="Year for analytics"),
    db: Session = Depends(get_db)
):
    access_token = get_user_etsy_token(current_user, db)
    return service.get_monthly_analytics(access_token, year, current_user.get_uuid(), db)

@router.get('/top-sellers', response_model=model.TopSellersResponse)
async def get_top_sellers(
    current_user: CurrentUser,
    year: int = Query(None, description="Year for top sellers"),
    db: Session = Depends(get_db)
):
    access_token = get_user_etsy_token(current_user, db)
    return service.get_top_sellers(access_token, year, current_user.get_uuid(), db)

@router.get('/shop-listings', response_model=model.ShopListingsResponse)
async def get_shop_listings(
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    access_token = get_user_etsy_token(current_user, db)
    return service.get_shop_listings(access_token, limit, offset, current_user.get_uuid(), db)
