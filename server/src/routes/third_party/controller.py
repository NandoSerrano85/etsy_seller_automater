from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from server.src.routes.auth.service import CurrentUser, verify_token, TokenData
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.services.cache_service import ApiCache
from . import model
from . import service
import logging


router = APIRouter(
    prefix='/third-party',
    tags=['third-party']
)

@router.get("/oauth-data", response_model=model.ThirdPartyOauthDataResponse)
async def get_oauth_data():
    """API endpoint to get OAuth configuration data for the frontend."""
    return service.get_oauth_data()

security = HTTPBearer(auto_error=False)

async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenData]:
    """Get current user if valid token is provided, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return verify_token(credentials.credentials)
    except:
        return None

@router.get('/oauth-redirect', response_model=model.ThirdPartyOauthResponse)
async def oauth_redirect(code: str, current_user: Optional[TokenData] = Depends(get_optional_current_user), db: Session = Depends(get_db)):
    try:
        logging.info(f"OAuth redirect called with code: {code[:10]}...")
        
        if not current_user:
            logging.warning("No authenticated user found, falling back to legacy flow")
            return service.oauth_redirect_legacy(code)
            
        user_id = current_user.get_uuid()
        if not user_id:
            logging.error("User ID missing from token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
            
        logging.info(f"Processing OAuth redirect for user {user_id}")
        response = service.oauth_redirect(code, user_id, db)
        
        if not response.success:
            logging.error(f"OAuth redirect failed: {response.message}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.message
            )
            
        return response
        
    except Exception as e:
        logging.error(f"Error in oauth_redirect endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get('/oauth-redirect-legacy', response_model=model.ThirdPartyOauthResponse)
async def oauth_redirect(code: str):
   return service.oauth_redirect_legacy(code)

@router.post('/oauth-callback', response_model=model.ThirdPartyOauthResponse)
async def oauth_callback(code: str, state: str):
   return service.oauth_callback(code, state)

@router.get('/verify-connection')
async def verify_etsy_connection(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Verify if the current Etsy connection is valid (cached for 5 minutes)"""
    user_id = str(current_user.get_uuid())

    # Try to get from cache first
    cached_result = await ApiCache.get_connection_cache(user_id)
    if cached_result is not None:
        logging.debug(f"Cache hit for verify-connection user {user_id}")
        return cached_result

    # Call service and cache result
    result = service.verify_etsy_connection(current_user.get_uuid(), db)

    # Cache successful results for 5 minutes, failed ones for 1 minute
    ttl = 300 if result.get('connected', False) else 60
    await ApiCache.set_connection_cache(user_id, result, ttl)

    logging.debug(f"Cached verify-connection result for user {user_id}")
    return result

@router.post('/revoke-token')
async def revoke_etsy_token(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Revoke Etsy access token and remove connection"""
    return service.revoke_etsy_token(current_user.get_uuid(), db)

@router.post('/refresh-shop-id')
async def refresh_shop_id(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Refresh and store the user's Etsy shop ID"""
    return service.refresh_shop_id(current_user.get_uuid(), db)