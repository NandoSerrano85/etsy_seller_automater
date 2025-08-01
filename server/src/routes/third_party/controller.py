from fastapi import APIRouter, Depends

from server.src.routes.auth.service import CurrentUser
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from . import model
from . import service


router = APIRouter(
    prefix='/third-party',
    tags=['third-party']
)

@router.get("/oauth-data", response_model=model.ThirdPartyOauthDataResponse)
async def get_oauth_data():
    """API endpoint to get OAuth configuration data for the frontend."""
    return service.get_oauth_data()

@router.get('/oauth-redirect', response_model=model.ThirdPartyOauthResponse)
async def oauth_redirect(code: str, current_user: CurrentUser, db: Session = Depends(get_db)):
   return service.oauth_redirect(code, current_user.get_uuid(), db)

@router.get('/oauth-redirect-legacy', response_model=model.ThirdPartyOauthResponse)
async def oauth_redirect(code: str):
   return service.oauth_redirect_legacy(code)

@router.post('/oauth-callback', response_model=model.ThirdPartyOauthResponse)
async def oauth_callback(code: str, state: str):
   return service.oauth_callback(code, state)