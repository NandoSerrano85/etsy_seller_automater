from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, requests, time, json
from pydantic import BaseModel
from typing import List, Dict, Any

# Import OAuth logic from etsy_oath_token
from server.engine.etsy_oath_token import get_oauth_variables, store_oauth_tokens

# Import mask utilities
from server.engine.mask_utils import save_mask_data, validate_mask_points

# Import constants
from server.constants import (
    OAUTH_CONFIG, 
    API_CONFIG, 
    SERVER_CONFIG, 
    PATHS, 
    ERROR_MESSAGES, 
    SUCCESS_MESSAGES,
    DEFAULTS
)

# Pydantic models for request validation
class MaskPoint(BaseModel):
    x: float
    y: float

class MaskData(BaseModel):
    masks: List[List[MaskPoint]]
    imageType: str

# Create the main FastAPI app
app = FastAPI(title="Etsy Seller Automaker", version="1.0.0")

# Get the project root directory (3 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mount static files for React frontend
frontend_build_path = os.path.join(project_root, PATHS['frontend_build'])
if os.path.exists(frontend_build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_path, "static")), name="static")

# API Routes
@app.get("/api/oauth-data")
async def get_oauth_data():
    """API endpoint to get OAuth configuration data for the frontend."""
    oauth_vars = get_oauth_variables()
    return {
        "clientId": oauth_vars['clientID'],
        "redirectUri": oauth_vars['redirectUri'],
        "state": oauth_vars['state'],
        "codeChallenge": oauth_vars['codeChallenge'],
        "scopes": OAUTH_CONFIG['scopes'],
        "codeChallengeMethod": OAUTH_CONFIG['code_challenge_method'],
        "responseType": OAUTH_CONFIG['response_type'],
        "oauthConnectUrl": API_CONFIG['oauth_connect_url']
    }

@app.get('/api/ping')
async def ping():
    """API endpoint to demonstrate an API call to a service."""
    oauth_vars = get_oauth_variables()
    headers = {'x-api-key': oauth_vars['clientID']}
    response = requests.get(API_CONFIG['ping_url'], headers=headers)
    if response.ok:
        return response.json()
    else:
        return {"error": "Failed to ping Etsy API"}

@app.get('/oauth/redirect')
async def oauth_redirect(code: str):
    """Handle OAuth redirect and token exchange."""
    oauth_vars = get_oauth_variables()
    
    authCode = code
    payload = {
        'grant_type': 'authorization_code',
        'client_id': oauth_vars['clientID'],
        'redirect_uri': oauth_vars['redirectUri'],
        'code': authCode,
        'code_verifier': oauth_vars['clientVerifier'],
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(API_CONFIG['token_url'], data=payload, headers=headers)
    if response.ok:
        tokenData = response.json()
        access_token = tokenData['access_token']
        refresh_token = tokenData.get('refresh_token')
        expires_in = tokenData.get('expires_in', DEFAULTS['default_expires_in'])
        
        # Store tokens using the centralized function
        store_oauth_tokens(access_token, refresh_token, expires_in)
        
        time.sleep(1)  # Add delay to ensure .env file is updated
        
        # Return JSON response for frontend
        return JSONResponse(content={
            "success": True,
            "access_token": access_token,
            "message": SUCCESS_MESSAGES['oauth_success']
        })
    else:
        print(f"Token exchange failed: {response.status_code} {response.text}")
        return JSONResponse(
            status_code=400,
            content={"error": ERROR_MESSAGES['token_exchange_failed'], "details": response.text}
        )

@app.get('/api/user-data')
async def get_user_data(access_token: str):
    """API endpoint to get user data for the frontend."""
    oauth_vars = get_oauth_variables()
    
    # Use the correct endpoint to get user data
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    url = f"{API_CONFIG['base_url']}/application/users/me"
    response = requests.get(url, headers=headers)
    if response.ok:
        userData = response.json()
        
        # Get shop info for display
        shop_name = os.getenv('SHOP_NAME')
        shop_url = os.getenv('SHOP_URL')
        
        return {
            "userData": userData,
            "shopInfo": {
                "shop_name": shop_name,
                "shop_url": shop_url
            }
        }
    else:
        print(f"Failed to fetch user data: {response.status_code} {response.text}")
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES['user_data_failed'])

@app.post('/api/masks')
async def create_masks(mask_data: MaskData):
    """API endpoint to save mask data from the React frontend."""
    try:
        # Convert MaskPoint objects to dictionaries
        masks_dict = []
        for mask_points in mask_data.masks:
            mask_dict = [{"x": point.x, "y": point.y} for point in mask_points]
            masks_dict.append(mask_dict)
        
        # Validate mask data
        for i, mask_points in enumerate(masks_dict):
            if not validate_mask_points(mask_points):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid mask data for mask {i + 1}. Need at least 3 valid points."
                )
        
        # Save mask data using utility function
        file_path = save_mask_data(masks_dict, mask_data.imageType)
        
        return {
            "success": True,
            "message": f"Successfully saved {len(masks_dict)} masks for {mask_data.imageType}",
            "masks_count": len(masks_dict),
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving masks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save masks: {str(e)}")

# Frontend Routes
@app.get("/")
async def serve_frontend():
    """Serve the React frontend."""
    index_path = os.path.join(frontend_build_path, 'index.html')
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Fallback if React build doesn't exist
        return {"message": ERROR_MESSAGES['frontend_not_built']}

@app.get("/{full_path:path}")
async def serve_frontend_routes(full_path: str):
    """Serve React routes for client-side routing."""
    index_path = os.path.join(frontend_build_path, 'index.html')
    
    # Don't serve index.html for API routes
    if full_path.startswith('api/') or full_path.startswith('oauth/'):
        raise HTTPException(status_code=404, detail="Not found")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": ERROR_MESSAGES['frontend_not_built']} 