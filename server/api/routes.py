from fastapi import FastAPI, APIRouter, Request, HTTPException, UploadFile, File, Form, Depends, Security, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os, requests, time, json, glob, tempfile, shutil, random
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from pprint import pprint
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging

# Import OAuth logic from etsy_oath_token
from server.engine.etsy_api_engine import EtsyAPI
from server.engine.etsy_oath_token import get_oauth_variables, store_oauth_tokens
from server.engine.gangsheet_engine import create_gang_sheets

# Import mask utilities
from server.engine.mask_utils import validate_mask_points
from server.engine.mask_db_utils import save_mask_data_to_db

# Import constants
from server.constants import (
    OAUTH_CONFIG, 
    API_CONFIG, 
    SERVER_CONFIG, 
    PATHS, 
    ERROR_MESSAGES, 
    SUCCESS_MESSAGES,
    DEFAULTS,
    # ETSY_TEMPLATES
)

# Import mockup engine
from server.engine.mockup_engine import process_uploaded_mockups

# Import models
from server.api.models import (
    Base, User, OAuthToken, EtsyTemplate, CanvasConfig, SizeConfig, 
    CanvasConfigCreate, CanvasConfigUpdate, CanvasConfigOut,
    SizeConfigCreate, SizeConfigUpdate, SizeConfigOut,
    get_db
)

# JWT settings and security
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'supersecretkey')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class MaskPoint(BaseModel):
    x: float
    y: float

class MaskData(BaseModel):
    masks: List[List[MaskPoint]]
    imageType: str

# --- EtsyTemplate CRUD API Models ---
class EtsyTemplateCreate(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    who_made: Optional[str] = None
    when_made: Optional[str] = None
    taxonomy_id: Optional[int] = None
    price: Optional[float] = None
    materials: Optional[Union[str, List[str]]] = None
    shop_section_id: Optional[int] = None
    quantity: Optional[int] = None
    tags: Optional[Union[str, List[str]]] = None
    item_weight: Optional[float] = None
    item_weight_unit: Optional[str] = None
    item_length: Optional[float] = None
    item_width: Optional[float] = None
    item_height: Optional[float] = None
    item_dimensions_unit: Optional[str] = None
    is_taxable: Optional[bool] = None
    type: Optional[str] = None
    processing_min: Optional[int] = None
    processing_max: Optional[int] = None
    return_policy_id: Optional[int] = None

class EtsyTemplateUpdate(EtsyTemplateCreate):
    pass

class EtsyTemplateOut(EtsyTemplateCreate):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or 'user_id' not in payload:
        print(f"DEBUG AUTH: Invalid token - payload: {payload}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload['user_id']).first()
    if not user:
        print(f"DEBUG AUTH: User not found for user_id: {payload['user_id']}")
        raise HTTPException(status_code=401, detail="User not found")
    print(f"DEBUG AUTH: User authenticated successfully: {user.id} ({user.shop_name})")
    return user

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Create the main FastAPI app
app = FastAPI(title="Etsy Seller Automaker", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory (3 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mount static files for React frontend
frontend_build_path = os.path.join(project_root, PATHS['frontend_build'])
static_path = os.path.join(project_root, 'server', 'static')

# Mount static files if they exist (for production builds)
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
elif os.path.exists(frontend_build_path):
    # Fallback to frontend build directory
    static_dir = os.path.join(frontend_build_path, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def log_routes():
    logging.basicConfig(level=logging.INFO)
    route_list = [route.path for route in app.routes]
    logging.info(f"FastAPI app started. Registered routes: {route_list}")
    print(f"FastAPI app started. Registered routes: {route_list}")

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

@app.get("/api/oauth-data-legacy")
async def get_oauth_data_legacy():
    """API endpoint to get OAuth configuration with legacy redirect URI for testing."""
    oauth_vars = get_oauth_variables()
    from server.engine.etsy_oath_token import get_redirect_uri_legacy
    return {
        "clientId": oauth_vars['clientID'],
        "redirectUri": get_redirect_uri_legacy(),
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
    print("DEBUG API: ping endpoint called")
    oauth_vars = get_oauth_variables()
    headers = {'x-api-key': oauth_vars['clientID']}
    response = requests.get(API_CONFIG['ping_url'], headers=headers)
    if response.ok:
        return response.json()
    else:
        return {"error": "Failed to ping Etsy API"}

@app.get('/api/test-debug')
async def test_debug():
    """Test endpoint to check if debug logging is working."""
    print("DEBUG API: test-debug endpoint called")
    return {"message": "Debug logging is working"}

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
        
        # Return JSON response with token data for frontend
        return JSONResponse(content={
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "message": SUCCESS_MESSAGES['oauth_success']
        })
    else:
        print(f"Token exchange failed: {response.status_code} {response.text}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": ERROR_MESSAGES['token_exchange_failed'], 
                "details": response.text
            }
        )

@app.post('/api/oauth-callback')
async def oauth_callback(request: Request):
    """API endpoint for frontend to handle OAuth callback."""
    try:
        body = await request.json()
        code = body.get('code')
        state = body.get('state')
        
        if not code:
            return JSONResponse(
                status_code=400,
                content={"error": "No authorization code provided"}
            )
        
        oauth_vars = get_oauth_variables()
        
        payload = {
            'grant_type': 'authorization_code',
            'client_id': oauth_vars['clientID'],
            'redirect_uri': oauth_vars['redirectUri'],
            'code': code,
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
    except Exception as e:
        print(f"Error in OAuth callback: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error during OAuth callback"}
        )

@app.get('/api/user-data')
async def get_user_data(access_token: str, current_user: User = Depends(get_current_user)):
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

@app.get('/api/top-sellers')
async def get_top_sellers(access_token: str, year: Optional[int] = None, current_user: User = Depends(get_current_user)):
    """API endpoint to get top sellers for the year."""
    oauth_vars = get_oauth_variables()
    
    if year is None:
        year = time.localtime().tm_year
    
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    try:
        # Get shop ID from environment
        shop_id = os.getenv('SHOP_ID')
        shop_name = os.getenv('SHOP_NAME')
        
        if not shop_id and not shop_name:
            raise HTTPException(status_code=400, detail="Shop ID or Shop Name not configured in .env file")
        
        # If we have shop_id, use it directly, otherwise get it from shop name
        if shop_id:
            final_shop_id = shop_id
        else:
            # Get shop data using shop name
            shop_url = f"{API_CONFIG['base_url']}/application/shops/{shop_name}"
            shop_response = requests.get(shop_url, headers=headers)
            if not shop_response.ok:
                print(f"Failed to fetch shop data: {shop_response.status_code} {shop_response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch shop data: {shop_response.text}")
            
            shop_data = shop_response.json()
            final_shop_id = shop_data['results'][0]['shop_id']
        
        print(f"Using shop ID: {final_shop_id}")
        
        # Get all transactions for the year using pagination
        transactions_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/receipts"
        
        # Convert dates to Unix timestamps
        start_timestamp = int(time.mktime(time.strptime(f"{year}-01-01", "%Y-%m-%d")))
        end_timestamp = int(time.mktime(time.strptime(f"{year}-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")))
        
        all_receipts = []
        offset = 0
        limit = 100  # Etsy API limit
        
        while True:
            params = {
                'limit': limit,
                'offset': offset,
                'min_created': start_timestamp,
                'max_created': end_timestamp
            }
            
            print(f"Fetching transactions from: {transactions_url}")
            print(f"With params: {params}")
            
            transactions_response = requests.get(transactions_url, headers=headers, params=params)
            if not transactions_response.ok:
                print(f"Failed to fetch transaction data: {transactions_response.status_code} {transactions_response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch transaction data: {transactions_response.text}")
            
            transactions_data = transactions_response.json()
            current_receipts = transactions_data.get('results', [])
            all_receipts.extend(current_receipts)
            
            print(f"Fetched {len(current_receipts)} receipts (offset: {offset})")
            
            # Check if we've got all receipts
            if len(current_receipts) < limit:
                break
                
            offset += limit
        
        print(f"Total receipts fetched: {len(all_receipts)}")
        
        # Process transactions to get top sellers
        item_sales = {}
        
        for receipt in all_receipts:
            total_qty = 0
            for transaction in receipt.get('transactions', []):
                total_qty += transaction.get('quantity', 1)
            discount_val = receipt['subtotal']['amount']//total_qty
            for transaction in receipt.get('transactions', []):
                listing_id = transaction.get('listing_id')
                title = transaction.get('title', 'Unknown Item')
                quantity = transaction.get('quantity', 1)
                price = float(transaction.get('price', {}).get('amount', 0))
                if listing_id not in item_sales:
                    item_sales[listing_id] = {
                        'title': title,
                        'quantity_sold': 0,
                        'total_amount': 0,
                        'total_discounts': 0
                    }
                
                item_sales[listing_id]['quantity_sold'] += quantity
                item_sales[listing_id]['total_amount'] += price * quantity
                item_sales[listing_id]['total_discounts'] += discount_val * quantity
        
        # Convert to list and sort by total amount (minus discounts)
        top_sellers = []
        for listing_id, data in item_sales.items():
            net_amount = data['total_amount'] - data['total_discounts']
            top_sellers.append({
                'listing_id': listing_id,
                'title': data['title'],
                'quantity_sold': data['quantity_sold'],
                'total_amount': data['total_amount'],
                'total_discounts': data['total_discounts'],
                'net_amount': net_amount
            })
        
        # Sort by net amount descending
        top_sellers.sort(key=lambda x: x['net_amount'], reverse=True)
        
        return {
            "year": year,
            "top_sellers": top_sellers,  # Return top 10
            "total_items": len(top_sellers)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching top sellers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch top sellers: {str(e)}")

@app.get('/api/shop-listings')
async def get_shop_listings(access_token: str, limit: int = 50, offset: int = 0, current_user: User = Depends(get_current_user)):
    """API endpoint to get shop listings/designs."""
    oauth_vars = get_oauth_variables()
    
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    try:
        shop_id = os.getenv('SHOP_ID')
        shop_name = current_user.shop_name
        
        if not shop_id and not shop_name:
            raise HTTPException(status_code=400, detail="Shop ID or Shop Name not configured in .env file")
        
        # If we have shop_id, use it directly, otherwise get it from shop name
        if shop_id:
            final_shop_id = shop_id
        else:
            # Get shop data using shop name
            shop_url = f"{API_CONFIG['base_url']}/application/shops/{shop_name}"
            shop_response = requests.get(shop_url, headers=headers)
            if not shop_response.ok:
                print(f"Failed to fetch shop data: {shop_response.status_code} {shop_response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch shop data: {shop_response.text}")
            
            shop_data = shop_response.json()
            final_shop_id = shop_data['results'][0]['shop_id']
        
        # Get shop listings using shop ID
        listings_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/listings/active"
        params = {
            'limit': limit,
            'offset': offset,
            'includes': 'Images'
        }
        
        response = requests.get(listings_url, headers=headers, params=params)
        if not response.ok:
            print(f"Failed to fetch shop listings: {response.status_code} {response.text}")
            raise HTTPException(status_code=400, detail=f"Failed to fetch shop listings: {response.text}")
        
        listings_data = response.json()
        
        # Get local images
        local_images_response = await get_local_images(current_user)
        local_images = local_images_response.get('images', [])
        
        # Process listings to get design information
        designs = []
        for listing in listings_data.get('results', []):
            design = {
                'listing_id': listing.get('listing_id'),
                'title': listing.get('title'),
                'description': listing.get('description'),
                'price': listing.get('price', {}).get('amount'),
                'currency': listing.get('price', {}).get('divisor'),
                'quantity': listing.get('quantity'),
                'state': listing.get('state'),
                'images': [],
                'local_images': []
            }
            
            # Get Etsy images
            for image in listing.get('Images', []):
                design['images'].append({
                    'url_full': image.get('url_fullxfull'),
                    'url_75': image.get('url_75x75'),
                    'url_170': image.get('url_170x135'),
                    'url_570': image.get('url_570xN'),
                    'url_640': image.get('url_640x640')
                })
            
            # Add local images (you can customize this logic based on your needs)
            # For now, we'll add all local images to each design
            design['local_images'] = local_images
            
            designs.append(design)
        
        return {
            "designs": designs,
            "count": len(designs),
            "total": listings_data.get('count', 0),
            "pagination": {
                "limit": limit,
                "offset": offset
            },
            "local_images_count": len(local_images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching shop listings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch shop listings: {str(e)}")

@app.post('/api/masks')
async def create_masks(mask_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # print(f"DEBUG API: Received mask data: {mask_data}")
    # Extract image size
    image_width = mask_data.get('imageWidth', 1000)
    image_height = mask_data.get('imageHeight', 1000)
    image_shape = (image_height, image_width)
    # Extract masks and points
    masks_data = mask_data.get('masks', [])
    starting_name = mask_data.get('starting_name', 100)
    template_name = mask_data.get('imageType', 'UVDTF 16oz')
    # Validate mask data
    for i, mask_points in enumerate(masks_data):
        if not validate_mask_points(mask_points):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid mask data for mask {i + 1}. Need at least 3 valid points."
            )
    # Save mask data to database
    mask_data_obj = save_mask_data_to_db(
        db=db,
        user_id=current_user.id,
        template_name=template_name,
        masks_data=masks_data,
        starting_name=starting_name,
        image_shape=image_shape
    )
    return {
        "success": True,
        "message": f"Successfully saved {len(masks_data)} masks for {template_name}",
        "masks_count": len(masks_data),
        "template_name": template_name,
        "mask_data_id": mask_data_obj.id
    }

@app.get('/api/user-mask-data')
async def get_user_mask_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """API endpoint to get all mask data for the current user."""
    try:
        from server.engine.mask_db_utils import get_user_mask_data
        
        mask_data_list = get_user_mask_data(db, current_user.id)
        
        # Convert to response format
        response_data = []
        for mask_data in mask_data_list:

            response_data.append({
                "id": mask_data.id,
                "template_name": mask_data.template_name,
                "masks_count": len(mask_data.masks) if mask_data.masks else 0,
                "points_count": len(mask_data.points) if mask_data.points else 0,
                "starting_name": mask_data.starting_name,
                "created_at": mask_data.created_at,
                "updated_at": mask_data.updated_at
            })
        
        return {
            "success": True,
            "mask_data": response_data
        }
        
    except Exception as e:
        print(f"Error getting user mask data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get mask data: {str(e)}")

@app.get('/api/user-mask-data/{template_name}')
async def get_user_mask_data_by_template(template_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """API endpoint to get mask data for a specific template."""
    try:
        from server.engine.mask_db_utils import load_mask_data_from_db, inspect_mask_data
        
        # First, let's inspect the raw data
        inspection = inspect_mask_data(db, current_user.id, template_name)
        # print(f"DEBUG API: Inspection result: {inspection}")
        
        masks, points_list, starting_name = load_mask_data_from_db(db, current_user.id, template_name)
        
        return {
            "success": True,
            "template_name": template_name,
            "masks_count": len(masks),
            "points_count": len(points_list),
            "starting_name": starting_name,
            "masks": masks,
            "points": points_list,
            "inspection": inspection
        }
        
    except ValueError as e:
        # No mask data found for this template
        return {
            "success": False,
            "template_name": template_name,
            "message": str(e)
        }
    except Exception as e:
        print(f"Error getting mask data for template {template_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get mask data: {str(e)}")

@app.delete('/api/user-mask-data/{template_name}')
async def delete_user_mask_data(template_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """API endpoint to delete mask data for a specific template."""
    try:
        from server.engine.mask_db_utils import delete_mask_data
        
        success = delete_mask_data(db, current_user.id, template_name)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully deleted mask data for template '{template_name}'"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"No mask data found for template '{template_name}'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting mask data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete mask data: {str(e)}")

@app.get('/api/create-gang-sheets')
async def get_etsy_item_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """API endpoint to get item summary from Etsy."""
    etsy_api = EtsyAPI()
    template = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id).first()
    template_name = template.name if template else "UVDTF 16oz"
    shop_name = current_user.shop_name
    local_root = os.getenv('LOCAL_ROOT_PATH')
    item_summary = etsy_api.fetch_open_orders_items(f"{local_root}{shop_name}/", template_name)
    try:
        create_gang_sheets(
            item_summary[template_name] if template_name in item_summary else item_summary.get("UVDTF 16oz", {}),
            template_name,
            f"{local_root}{shop_name}/Printfiles/",
            item_summary["Total QTY"] if item_summary else 0
        )
    except Exception as e:
        print(f"Error creating gang sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create gang sheets: {str(e)}")
    return item_summary

@app.get('/api/local-images/{filename}')
async def serve_local_image(filename: str, token: str = Query(None)):
    """API endpoint to serve local PNG images."""
    print(f"DEBUG API: Endpoint called for filename: {filename}")
    print(f"DEBUG API: Token provided: {token is not None}")
    
    try:
        # If no token provided, try to get user from headers
        current_user = None
        if token:
            try:
                payload = decode_access_token(token)
                if payload and 'user_id' in payload:
                    db = next(get_db())
                    current_user = db.query(User).filter(User.id == payload['user_id']).first()
                    print(f"DEBUG API: User authenticated: {current_user.id if current_user else 'None'}")
            except Exception as e:
                print(f"DEBUG API: Token validation failed: {e}")
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        print(f"DEBUG API: Serving image {filename} for user {current_user.id} ({current_user.shop_name})")
        base_path = f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/"
        print(f"DEBUG API: Checking template directory: {base_path}")
        if os.path.exists(base_path):
            for root, dirs, files in os.walk(base_path):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    print(f"DEBUG API: Found image at: {file_path}")
                    # Determine content type based on file extension
                    content_type = "image/png"  # default
                    if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                        content_type = "image/jpeg"
                    elif filename.lower().endswith('.gif'):
                        content_type = "image/gif"
                    elif filename.lower().endswith('.webp'):
                        content_type = "image/webp"
                    
                    headers = {
                        "Cache-Control": "public, max-age=3600",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET",
                        "Access-Control-Allow-Headers": "*"
                    }
                    
                    return FileResponse(
                        file_path, 
                        media_type=content_type,
                        headers=headers
                    )
        
        print(f"DEBUG API: Image {filename} not found for user {current_user.shop_name}")
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        print(f"Error serving image {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving image")

@app.get('/api/local-images')
async def get_local_images(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """API endpoint to get list of local PNG images."""
    print(f"DEBUG API: get_local_images endpoint called for user {current_user.id}")
    try:
        db = next(get_db())
        templates = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id).all()
        all_images = []
        shop_name = current_user.shop_name
        local_root = os.getenv('LOCAL_ROOT_PATH')
        
        # Create a token for image URLs
        token = create_access_token({"user_id": current_user.id})
        
        # Then check template directories
        for template in templates:
            images_path = f"{local_root}{shop_name}/{template.name}/"
            print(f"DEBUG API: Checking template path: {images_path}")
            if os.path.exists(images_path):
                png_files = glob.glob(os.path.join(images_path, "*.png"))
                print(f"DEBUG API: Found {len(png_files)} PNG files in template {template.name}")
                for file_path in png_files:
                    filename = os.path.basename(file_path)
                    all_images.append({
                        "filename": filename,
                        "path": f"/api/local-images/{filename}?token={token}",  # Include token in URL
                        "full_path": file_path,
                        "template_name": template.name,
                        "template_title": template.template_title
                    })
        
        print(f"DEBUG API: Total images found: {len(all_images)}")
        return {"images": all_images}
    except Exception as e:
        print(f"Error getting local images: {str(e)}")
        return {"images": [], "error": str(e)}

@app.get('/api/monthly-analytics')
async def get_monthly_analytics(access_token: str, year: Optional[int] = None, current_user: User = Depends(get_current_user)):
    """API endpoint to get monthly analytics for the year."""
    oauth_vars = get_oauth_variables()
    
    if year is None:
        year = time.localtime().tm_year
    
    print(f"Monthly analytics request - Year: {year}, Access token: {access_token[:20]}...")
    
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    try:
        # Get shop ID from environment
        shop_id = os.getenv('SHOP_ID')
        shop_name = os.getenv('SHOP_NAME')
        
        print(f"Shop ID: {shop_id}, Shop Name: {shop_name}")
        
        if not shop_id and not shop_name:
            raise HTTPException(status_code=400, detail="Shop ID or Shop Name not configured in .env file")
        
        # If we have shop_id, use it directly, otherwise get it from shop name
        if shop_id:
            final_shop_id = shop_id
            print(f"Using shop ID from env: {final_shop_id}")
        else:
            # Get shop data using shop name
            shop_url = f"{API_CONFIG['base_url']}/application/shops/{shop_name}"
            print(f"Fetching shop data from: {shop_url}")
            shop_response = requests.get(shop_url, headers=headers)
            if not shop_response.ok:
                print(f"Failed to fetch shop data: {shop_response.status_code} {shop_response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch shop data: {shop_response.text}")
            
            shop_data = shop_response.json()
            final_shop_id = shop_data['results'][0]['shop_id']
            print(f"Got shop ID from API: {final_shop_id}")
        
        # Get all transactions for the year using pagination
        transactions_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/receipts"
        
        # Convert dates to Unix timestamps
        start_timestamp = int(time.mktime(time.strptime(f"{year}-01-01", "%Y-%m-%d")))
        end_timestamp = int(time.mktime(time.strptime(f"{year}-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")))
        
        all_receipts = []
        offset = 0
        limit = 100  # Etsy API limit
        
        while True:
            params = {
                'limit': limit,
                'offset': offset,
                'min_created': start_timestamp,
                'max_created': end_timestamp
            }
            
            print(f"Fetching transactions from: {transactions_url}")
            print(f"With params: {params}")
            
            transactions_response = requests.get(transactions_url, headers=headers, params=params)
            if not transactions_response.ok:
                print(f"Failed to fetch transaction data: {transactions_response.status_code} {transactions_response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch transaction data: {transactions_response.text}")
            
            transactions_data = transactions_response.json()
            current_receipts = transactions_data.get('results', [])
            all_receipts.extend(current_receipts)
            
            print(f"Fetched {len(current_receipts)} receipts (offset: {offset})")
            
            # Check if we've got all receipts
            if len(current_receipts) < limit:
                break
                
            offset += limit
        
        print(f"Total receipts fetched: {len(all_receipts)}")
        
        # Initialize monthly data
        monthly_data = {}
        for month in range(1, 13):
            monthly_data[month] = {
                'total_sales': 0,
                'total_quantity': 0,
                'total_discounts': 0,
                'net_sales': 0,
                'item_sales': {},
                'receipt_count': 0
            }
        
        # Process transactions by month
        for receipt in all_receipts:
            # Convert timestamp to month
            receipt_date = time.localtime(receipt.get('created_timestamp', 0))
            month = receipt_date.tm_mon
            
            if month in monthly_data:
                monthly_data[month]['receipt_count'] += 1
                
                total_qty = 0
                for transaction in receipt.get('transactions', []):
                    total_qty += transaction.get('quantity', 1)
                
                discount_val = receipt['subtotal']['amount'] // total_qty if total_qty > 0 else 0
                
                for transaction in receipt.get('transactions', []):
                    listing_id = transaction.get('listing_id')
                    title = transaction.get('title', 'Unknown Item')
                    quantity = transaction.get('quantity', 1)
                    price = float(transaction.get('price', {}).get('amount', 0))
                    
                    # Update monthly totals
                    monthly_data[month]['total_sales'] += price * quantity
                    monthly_data[month]['total_quantity'] += quantity
                    monthly_data[month]['total_discounts'] += discount_val * quantity
                    
                    # Track item sales by month
                    if listing_id not in monthly_data[month]['item_sales']:
                        monthly_data[month]['item_sales'][listing_id] = {
                            'title': title,
                            'quantity_sold': 0,
                            'total_amount': 0,
                            'total_discounts': 0
                        }
                    
                    monthly_data[month]['item_sales'][listing_id]['quantity_sold'] += quantity
                    monthly_data[month]['item_sales'][listing_id]['total_amount'] += price * quantity
                    monthly_data[month]['item_sales'][listing_id]['total_discounts'] += discount_val * quantity
        
        # Calculate net sales and prepare response
        monthly_breakdown = []
        total_year_sales = 0
        total_year_quantity = 0
        total_year_discounts = 0
        total_year_net = 0
        
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        for month in range(1, 13):
            month_data = monthly_data[month]
            month_data['net_sales'] = month_data['total_sales'] - month_data['total_discounts']
            
            # Get top 5 items for this month
            top_items = []
            for listing_id, item_data in month_data['item_sales'].items():
                net_amount = item_data['total_amount'] - item_data['total_discounts']
                top_items.append({
                    'listing_id': listing_id,
                    'title': item_data['title'],
                    'quantity_sold': item_data['quantity_sold'],
                    'total_amount': item_data['total_amount'],
                    'total_discounts': item_data['total_discounts'],
                    'net_amount': net_amount
                })
            
            # Sort by net amount descending
            top_items.sort(key=lambda x: x['net_amount'], reverse=True)
            
            monthly_breakdown.append({
                'month': month,
                'month_name': month_names[month - 1],
                'total_sales': month_data['total_sales'],
                'total_quantity': month_data['total_quantity'],
                'total_discounts': month_data['total_discounts'],
                'net_sales': month_data['net_sales'],
                'receipt_count': month_data['receipt_count'],
                'top_items': top_items[:5]  # Top 5 items per month
            })
            
            # Add to year totals
            total_year_sales += month_data['total_sales']
            total_year_quantity += month_data['total_quantity']
            total_year_discounts += month_data['total_discounts']
            total_year_net += month_data['net_sales']
        
        # Get overall top sellers for the year
        all_item_sales = {}
        for receipt in all_receipts:
            total_qty = 0
            for transaction in receipt.get('transactions', []):
                total_qty += transaction.get('quantity', 1)
            discount_val = receipt['subtotal']['amount'] // total_qty if total_qty > 0 else 0
            
            for transaction in receipt.get('transactions', []):
                listing_id = transaction.get('listing_id')
                title = transaction.get('title', 'Unknown Item')
                quantity = transaction.get('quantity', 1)
                price = float(transaction.get('price', {}).get('amount', 0))
                
                if listing_id not in all_item_sales:
                    all_item_sales[listing_id] = {
                        'title': title,
                        'quantity_sold': 0,
                        'total_amount': 0,
                        'total_discounts': 0
                    }
                
                all_item_sales[listing_id]['quantity_sold'] += quantity
                all_item_sales[listing_id]['total_amount'] += price * quantity
                all_item_sales[listing_id]['total_discounts'] += discount_val * quantity
        
        # Convert to list and sort by net amount
        year_top_sellers = []
        for listing_id, data in all_item_sales.items():
            net_amount = data['total_amount'] - data['total_discounts']
            year_top_sellers.append({
                'listing_id': listing_id,
                'title': data['title'],
                'quantity_sold': data['quantity_sold'],
                'total_amount': data['total_amount'],
                'total_discounts': data['total_discounts'],
                'net_amount': net_amount
            })
        
        year_top_sellers.sort(key=lambda x: x['net_amount'], reverse=True)
        
        print(f"Successfully processed monthly analytics. Year totals: Sales={total_year_sales}, Quantity={total_year_quantity}, Net={total_year_net}")
        
        return {
            "year": year,
            "summary": {
                "total_sales": total_year_sales,
                "total_quantity": total_year_quantity,
                "total_discounts": total_year_discounts,
                "net_sales": total_year_net,
                "total_receipts": sum(month['receipt_count'] for month in monthly_breakdown)
            },
            "monthly_breakdown": monthly_breakdown,
            "year_top_sellers": year_top_sellers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching monthly analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch monthly analytics: {str(e)}")

@app.get('/api/mockup-images')
async def get_mockup_images(current_user: User = Depends(get_current_user)):
    """API endpoint to get list of local mockup images."""
    print(f"DEBUG API: get_mockup_images endpoint called for user {current_user.id}")
    try:
        mockup_path = f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/Mockups/Cup Wraps/"
        print(f"DEBUG API: Checking mockup path: {mockup_path}")
        if not os.path.exists(mockup_path):
            print(f"DEBUG API: Mockup path does not exist")
            return {"images": [], "error": "Mockup images directory not found"}
        files = [f for f in os.listdir(mockup_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"DEBUG API: Found {len(files)} mockup files")
        
        # Create a token for image URLs
        token = create_access_token({"user_id": current_user.id})
        
        images = []
        for f in files:
            images.append({
                "filename": f,
                "url": f"/api/mockup-images/{f}?token={token}"  # Include token in URL
            })
        
        return {"images": images}
    except Exception as e:
        print(f"Error getting mockup images: {str(e)}")
        return {"images": [], "error": str(e)}

@app.get('/api/mockup-images/{filename}')
async def serve_mockup_image(filename: str, token: str = Query(None)):
    """API endpoint to serve local mockup images."""
    try:
        # If no token provided, try to get user from headers
        current_user = None
        if token:
            try:
                payload = decode_access_token(token)
                if payload and 'user_id' in payload:
                    db = next(get_db())
                    current_user = db.query(User).filter(User.id == payload['user_id']).first()
                    print(f"DEBUG API: User authenticated: {current_user.id if current_user else 'None'}")
            except Exception as e:
                print(f"DEBUG API: Token validation failed: {e}")
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        mockup_path = f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/Mockups/Cup Wraps/"
        file_path = os.path.join(mockup_path, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine content type based on file extension
        content_type = "image/png"  # default
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        headers = {
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*"
        }
        
        return FileResponse(
            file_path, 
            media_type=content_type,
            headers=headers
        )
    except Exception as e:
        print(f"Error serving mockup image {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving mockup image")

@app.post('/api/upload-mockup')
async def upload_mockup(files: List[UploadFile] = File(...), template_name: str = Form('UVDTF 16oz'), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    print(f"DEBUG API: upload-mockup endpoint called")
    print(f"DEBUG API: User: {current_user.id} ({current_user.shop_name})")
    print(f"DEBUG API: Template name: {template_name}")
    print(f"DEBUG API: Number of files: {len(files)}")
    
    try:
        # Get template to check if it's digital
        template = db.query(EtsyTemplate).filter(
            EtsyTemplate.user_id == current_user.id,
            EtsyTemplate.name == template_name
        ).first()
        
        print(f"DEBUG API: Template found: {template is not None}")
        if not template:
            print(f"DEBUG API: Template not found for name: {template_name}")
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        is_digital = template.type == 'digital'
        print(f"DEBUG API: Template type: {template.type}, is_digital: {is_digital}")
        
        # Create appropriate directories based on template type
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        if not local_root_path:
            raise HTTPException(status_code=500, detail="LOCAL_ROOT_PATH environment variable not set")
            
        image_dir = f"{local_root_path}{current_user.shop_name}/Origin/16oz/"
        os.makedirs(image_dir, exist_ok=True)
        
        uploaded_file_paths = []
        digital_file_paths = []
        
        print(f"DEBUG API: Processing {len(files)} files")
        for i, file in enumerate(files):
            print(f"DEBUG API: Processing file {i+1}: {file.filename}")
            if not file.filename:
                print(f"DEBUG API: Skipping file {i+1} - no filename")
                continue  # Skip files without names
                
            # Save to mockup directory (for both physical and digital)
            image_file_path = os.path.join(image_dir, file.filename)
            print(f"DEBUG API: Saving file to: {image_file_path}")
            with open(image_file_path, "wb") as f:
                file_content = await file.read()
                f.write(file_content)
                print(f"DEBUG API: File saved, size: {len(file_content)} bytes")
            uploaded_file_paths.append(image_file_path)
            
        print(f"DEBUG API: Calling process_uploaded_mockups with {len(uploaded_file_paths)} files")
        result = process_uploaded_mockups(
            uploaded_file_paths,
            f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/",
            template_name,
            is_digital=is_digital,
            user_id=current_user.id,
            db=db
        )
        print(f"DEBUG API: process_uploaded_mockups returned: {result}")
        
        print(f"DEBUG API: finished processing uploaded files")
        print(f"DEBUG API: Starting Etsy API calls")
        etsy_api = EtsyAPI()
        # Fetch the user's template by name
        template = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id, EtsyTemplate.name == template_name).first()
        if not template:
            print(f"DEBUG API: Template not found for Etsy API calls")
            return JSONResponse(status_code=400, content={"success": False, "error": f"No template named '{template_name}' found for this user."})
        # Parse materials and tags from string to list if needed
        materials = template.materials.split(',') if template.materials else []
        tags = template.tags.split(',') if template.tags else []
        print(f"DEBUG API: Creating Etsy listings for {len(result)} designs")
        for i, (design, mockups) in enumerate(result.items()):
            print(f"DEBUG API: Creating listing {i+1}/{len(result)} for design: {design}")
            title = design.split(' ')[:2] if not is_digital else design.split('.')[0]
            listing_response = etsy_api.create_draft_listing(
                title=' '.join(title + [template.title]) if template.title else ' '.join(title),
                description=template.description,
                price=template.price,
                quantity=template.quantity,
                tags=tags,
                materials=materials,
                is_digital=is_digital,
                when_made=template.when_made,
                )
            listing_id = listing_response["listing_id"]
            print(f"DEBUG API: Created listing {listing_id}, uploading {len(mockups)} images")
            for j, mockup in enumerate(random.sample(mockups, len(mockups))):
                print(f"DEBUG API: Uploading image {j+1}/{len(mockups)} to listing {listing_id}")
                etsy_api.upload_listing_image(listing_id, mockup)
            print(f"DEBUG API: Completed listing {i+1}")

            # Upload digital file(s) if digital template
            if is_digital:
                # The digital file path and name are the key (design) in result.items()
                digital_file_path = os.path.join(f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/Digital/{template_name}/", design)
                digital_file_name = design
                print(f"DEBUG API: Uploading digital file {digital_file_name} to listing {listing_id}")
                try:
                    etsy_api.upload_listing_file(listing_id, digital_file_path, digital_file_name)
                    print(f"DEBUG API: Successfully uploaded digital file {digital_file_name} to listing {listing_id}")
                except Exception as e:
                    print(f"DEBUG API: Failed to upload digital file {digital_file_name} to listing {listing_id}: {e}")

        for filename in os.listdir(image_dir):
            file_path = os.path.join(image_dir, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Error deleting file {filename}: {e}")
        print(f"DEBUG API: Returning success response")
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "result": {
                    "message": f"Successfully processed {len(uploaded_file_paths)} files",
                    "files_processed": len(uploaded_file_paths),
                    "designs_created": len(result)
                }
            }
        )
    except Exception as e:
        print(f"DEBUG API: Error in upload-mockup: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Server error: {str(e)}"}
        )

@app.get('/api/orders')
async def get_orders(access_token: str, current_user: User = Depends(get_current_user)):
    """API endpoint to get active orders from Etsy."""
    oauth_vars = get_oauth_variables()
    
    headers = {
        'x-api-key': oauth_vars['clientID'],
        'Authorization': f'Bearer {access_token}',
    }
    
    try:
        # Get shop ID from environment
        shop_id = os.getenv('SHOP_ID')
        shop_name = os.getenv('SHOP_NAME')
        
        if not shop_id and not shop_name:
            raise HTTPException(status_code=400, detail="Shop ID or Shop Name not configured in .env file")
        
        # If we have shop_id, use it directly, otherwise get it from shop name
        if shop_id:
            final_shop_id = shop_id
        else:
            # Get shop data using shop name
            shop_url = f"{API_CONFIG['base_url']}/application/shops/{shop_name}"
            shop_response = requests.get(shop_url, headers=headers)
            if not shop_response.ok:
                print(f"Failed to fetch shop data: {shop_response.status_code} {shop_response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch shop data: {shop_response.text}")
            
            shop_data = shop_response.json()
            final_shop_id = shop_data['results'][0]['shop_id']
        
        # Get active receipts (orders)
        receipts_url = f"{API_CONFIG['base_url']}/application/shops/{final_shop_id}/receipts"
        params = {
            'limit': 100,
            'offset': 0,
            'was_paid': 'true',
            'was_shipped': 'false',
            'was_canceled': 'false'  # Only get open/active orders
        }
        
        response = requests.get(receipts_url, headers=headers, params=params)
        if not response.ok:
            print(f"Failed to fetch orders: {response.status_code} {response.text}")
            raise HTTPException(status_code=400, detail=f"Failed to fetch orders: {response.text}")
        
        receipts_data = response.json()
        
        # Process orders
        orders = []
        for receipt in receipts_data.get('results', []):
            order = {
                'order_id': receipt.get('receipt_id'),
                'order_date': receipt.get('created_timestamp'),
                'shipping_method': receipt.get('shipping_carrier', 'N/A'),
                'shipping_cost': receipt.get('total_shipping_cost', {}).get('amount', 0),
                'customer_name': receipt.get('name', 'N/A'),
                'items': []
            }
            
            # Get items in the order
            for transaction in receipt.get('transactions', []):
                item = {
                    'title': transaction.get('title', 'N/A'),
                    'quantity': transaction.get('quantity', 0),
                    'price': transaction.get('price', {}).get('amount', 0),
                    'listing_id': transaction.get('listing_id')
                }
                order['items'].append(item)
            
            orders.append(order)
        
        return {
            "orders": orders,
            "count": len(orders),
            "total": receipts_data.get('count', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

# Frontend Routes
class UserCreate(BaseModel):
    email: str
    password: str
    shop_name: str

class UserLogin(BaseModel):
    email: str
    password: str

@app.post('/api/register')
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Validate shop_name
    if not user.shop_name or not isinstance(user.shop_name, str) or not user.shop_name.strip():
        return {"success": False, "error": "shop_name is required and must be a non-empty string."}
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        return {"success": False, "error": "User already exists."}
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, shop_name=user.shop_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"success": True, "user_id": db_user.id, "email": db_user.email, "shop_name": db_user.shop_name}

@app.post('/api/login')
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    normalized_email = user.email.strip().lower()
    db_user = db.query(User).filter(User.email == normalized_email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": db_user.email, "user_id": db_user.id})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "shop_name": db_user.shop_name,
            "created_at": db_user.created_at
        }
    }

@app.get("/api/verify-token")
def verify_token(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/login"))):
    try:
        # Replace 'your-secret-key' and 'HS256' with your actual values
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload  # or return user info as needed
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# --- Password Change Models ---
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

# --- Password Change Endpoint ---
@app.post('/api/change-password')
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API endpoint to change user password."""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Validate new password
        if len(password_data.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")
        
        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)
        
        # Update user password
        current_user.hashed_password = new_hashed_password
        db.commit()
        
        return {"success": True, "message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")

# --- Enhanced User Templates Endpoints ---
@app.get('/api/user-templates', response_model=List[EtsyTemplateOut])
def list_user_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all templates for the current user."""
    try:
        templates = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id).all()
        return templates
    except Exception as e:
        print(f"Error fetching user templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")

@app.get('/api/user-templates/{template_id}', response_model=EtsyTemplateOut)
def get_user_template(template_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific template by ID for the current user."""
    try:
        template = db.query(EtsyTemplate).filter(
            EtsyTemplate.id == template_id, 
            EtsyTemplate.user_id == current_user.id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail='Template not found')
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch template")

@app.post('/api/user-templates', response_model=EtsyTemplateOut)
def create_user_template(template: EtsyTemplateCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new template for the current user."""
    try:
        # Check if template name already exists for this user
        existing_template = db.query(EtsyTemplate).filter(
            EtsyTemplate.user_id == current_user.id,
            EtsyTemplate.name == template.name
        ).first()
        
        if existing_template:
            raise HTTPException(status_code=400, detail=f"Template with name '{template.name}' already exists")
        
        # Handle materials and tags conversion
        materials_str = None
        if template.materials:
            if isinstance(template.materials, list):
                materials_str = ','.join(str(item) for item in template.materials if item)
            else:
                materials_str = str(template.materials)
        
        tags_str = None
        if template.tags:
            if isinstance(template.tags, list):
                tags_str = ','.join(str(item) for item in template.tags if item)
            else:
                tags_str = str(template.tags)
        
        db_template = EtsyTemplate(
            user_id=current_user.id,
            name=template.name,
            title=template.title,
            description=template.description,
            who_made=template.who_made,
            when_made=template.when_made,
            taxonomy_id=template.taxonomy_id,
            price=template.price,
            materials=materials_str,
            shop_section_id=template.shop_section_id,
            quantity=template.quantity,
            tags=tags_str,
            item_weight=template.item_weight,
            item_weight_unit=template.item_weight_unit,
            item_length=template.item_length,
            item_width=template.item_width,
            item_height=template.item_height,
            item_dimensions_unit=template.item_dimensions_unit,
            is_taxable=template.is_taxable,
            type=template.type,
            processing_min=template.processing_min,
            processing_max=template.processing_max,
            return_policy_id=template.return_policy_id
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return db_template
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create template")

@app.put('/api/user-templates/{template_id}', response_model=EtsyTemplateOut)
def update_user_template(template_id: int, template: EtsyTemplateUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update an existing template for the current user."""
    try:
        db_template = db.query(EtsyTemplate).filter(
            EtsyTemplate.id == template_id, 
            EtsyTemplate.user_id == current_user.id
        ).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail='Template not found')
        
        # Check if new name conflicts with existing template (excluding current template)
        if template.name != db_template.name:
            existing_template = db.query(EtsyTemplate).filter(
                EtsyTemplate.user_id == current_user.id,
                EtsyTemplate.name == template.name,
                EtsyTemplate.id != template_id
            ).first()
            
            if existing_template:
                raise HTTPException(status_code=400, detail=f"Template with name '{template.name}' already exists")
        
        # Update template fields
        for field, value in template.dict(exclude_unset=True).items():
            if field == 'materials' and value is not None:
                if isinstance(value, list):
                    setattr(db_template, field, ','.join(str(item) for item in value if item))
                else:
                    setattr(db_template, field, str(value))
            elif field == 'tags' and value is not None:
                if isinstance(value, list):
                    setattr(db_template, field, ','.join(str(item) for item in value if item))
                else:
                    setattr(db_template, field, str(value))
            else:
                setattr(db_template, field, value)
        
        db.commit()
        db.refresh(db_template)
        
        return db_template
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update template")

@app.delete('/api/user-templates/{template_id}')
def delete_user_template(template_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a template for the current user."""
    try:
        db_template = db.query(EtsyTemplate).filter(
            EtsyTemplate.id == template_id, 
            EtsyTemplate.user_id == current_user.id
        ).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail='Template not found')
        
        db.delete(db_template)
        db.commit()
        
        return {'success': True, 'message': 'Template deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete template")

# --- Default Template Creation Endpoint ---
@app.post('/api/user-templates/default')
def create_default_template(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a default UVDTF 16oz template for new users."""
    try:
        # Check if default template already exists
        existing_template = db.query(EtsyTemplate).filter(
            EtsyTemplate.user_id == current_user.id,
            EtsyTemplate.name == 'UVDTF 16oz'
        ).first()
        
        if existing_template:
            raise HTTPException(status_code=400, detail="Default template already exists")
        
        # Create default template from old constants
        default_template = EtsyTemplate(
            user_id=current_user.id,
            name='UVDTF 16oz',
            title='| UVDTF Cup wrap | Ready to apply | High Quality | Double Sided | Easy application | Cup Transfer | Waterproof',
            description="""*** Details ***
 - This listing is for a physical single 16 oz UV DTF cup wrap transfer. Cup, straw, lid are NOT included.
 - UV DTF cup wraps are an approximate measurement of 9.5" wide and 4.3" tall, perfect for 16 oz glass & acrylic cans.
 - UV DTF products are permanent & waterproof.

 *** Note ***
 - Not all 16 oz glass & acrylic cans are the same dimensions, please make sure to check your measurements before purchase.
 - All orders are printed in house on commercial UV DTF printers with high quality materials.
 - Printed colors and design resolution may appear slightly different from your phone, tablet or computer screen/monitor.

*** Care Instructions ***
- All UV DTF transfers are not dishwasher or microwave safe. Hand wash only.

*** Policy ***
 - Seller is not responsible for any application errors or any errors that may occur during placement of UV DTF transfer.
 - Seller is not responsible for any wear and tear of UV DTF transfer.
 - Seller is not responsible for any improper storage of transfer.
 - Seller is not responsible for care of UV DTF transfer after applied to the surface.
 - All claims require photos and/or videos to be considered for reprint or refund at seller's discretion.
 - All orders have a 48 hour window after receiving your order to make us aware of any issues such as missing or damaged transfers.
 - All orders go through multiple stages of quality and accuracy checks before packing and shipping of orders to ensure the highest quality service.

*** Shipping Policy ***
 - Seller is not responsible for lost, late arriving, stolen or damaged packages caused by USPS, UPS, FedEx or other carrier your order is shipped with. Buyer will need to file a claim with the carrier in the event packages do not arrive, are misdelivered, lost, stolen, damaged, etc. Once a package has a scan acceptance by the carrier, the seller is no longer responsible for the order. Please purchase shipping insurance whenever possible to ensure your order can be reshipped in these cases.

*** Thank You ***
Thank you so much! Your purchase truly means the world to me & my family and it helps my small business grow! Please make sure to explore our other UV DTF and DTF transfer options from wraps to decals and shirt transfers for all sizes.""",
            who_made='i_did',
            when_made='made_to_order',
            taxonomy_id=1,
            price=4.00,
            materials='UV DTF',
            shop_section_id=2,
            quantity=100,
            tags='UV DTF,Cup Wrap,Waterproof,Permanent,Transfer,Prints,Wholesale,Mug,16oz,17oz',
            item_weight=2.5,
            item_weight_unit='oz',
            item_length=11,
            item_width=9.5,
            item_height=1,
            item_dimensions_unit='in',
            is_taxable=True,
            type='physical',
            processing_min=1,
            processing_max=3,
            return_policy_id=None
        )
        
        db.add(default_template)
        db.commit()
        db.refresh(default_template)
        
        return {'success': True, 'message': 'Default template created successfully', 'template_id': default_template.id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating default template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create default template")

@app.get('/api/base-mockups/{template_name}')
async def list_base_mockups(template_name: str, current_user: User = Depends(get_current_user)):
    """List available base mockup images for a given Etsy template name."""
    base_dir = f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/Mockups/BaseMockups/{template_name}/"
    if not os.path.exists(base_dir):
        return {"images": []}
    
    files = [f for f in os.listdir(base_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Create a token for image URLs
    token = create_access_token({"user_id": current_user.id})
    
    images = []
    for f in files:
        images.append({
            "filename": f,
            "url": f"/api/base-mockup-image/{template_name}/{f}?token={token}"  # Include token in URL
        })
    
    return {"images": images}

@app.get('/api/base-mockup-image/{template_name}/{filename}')
async def serve_base_mockup_image(template_name: str, filename: str, token: str = Query(None)):
    """Serve a base mockup image by template name and filename."""
    try:
        # If no token provided, try to get user from headers
        current_user = None
        if token:
            try:
                payload = decode_access_token(token)
                if payload and 'user_id' in payload:
                    db = next(get_db())
                    current_user = db.query(User).filter(User.id == payload['user_id']).first()
                    print(f"DEBUG API: User authenticated: {current_user.id if current_user else 'None'}")
            except Exception as e:
                print(f"DEBUG API: Token validation failed: {e}")
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        base_dir = f"{os.getenv('LOCAL_ROOT_PATH')}{current_user.shop_name}/Mockups/BaseMockups/{template_name}/"
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine content type based on file extension
        content_type = "image/png"  # default
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        headers = {
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*"
        }
        
        return FileResponse(
            file_path, 
            media_type=content_type,
            headers=headers
        )
    except Exception as img_error:
        print(f"Error reading base mockup image {file_path}: {img_error}")
        raise HTTPException(status_code=500, detail="Error serving image")

# Example usage for a protected endpoint:
# @app.get('/api/protected')
# def protected_route(current_user: User = Depends(get_current_user)):
#     return {"message": f"Hello, {current_user.email}"}

# --- Canvas Configuration API Endpoints ---
@app.get('/api/canvas-configs', response_model=List[CanvasConfigOut])
def list_canvas_configs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all canvas configurations for the current user."""
    try:
        canvas_configs = db.query(CanvasConfig).filter(
            CanvasConfig.user_id == current_user.id,
            CanvasConfig.is_active == True
        ).all()
        return canvas_configs
    except Exception as e:
        print(f"Error listing canvas configs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list canvas configurations")

@app.get('/api/canvas-configs/{config_id}', response_model=CanvasConfigOut)
def get_canvas_config(config_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific canvas configuration by ID."""
    try:
        canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.id == config_id,
            CanvasConfig.user_id == current_user.id
        ).first()
        
        if not canvas_config:
            raise HTTPException(status_code=404, detail="Canvas configuration not found")
        
        return canvas_config
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting canvas config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get canvas configuration")

@app.post('/api/canvas-configs', response_model=CanvasConfigOut)
def create_canvas_config(canvas_config: CanvasConfigCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new canvas configuration."""
    try:
        # Check if template already exists for this user
        existing_config = db.query(CanvasConfig).filter(
            CanvasConfig.user_id == current_user.id,
            CanvasConfig.template_name == canvas_config.template_name,
            CanvasConfig.is_active == True
        ).first()
    
        if existing_config:
            raise HTTPException(status_code=400, detail="Canvas configuration already exists for this template")
        
        new_canvas_config = CanvasConfig(
            user_id=current_user.id,
            template_name=canvas_config.template_name,
            width_inches=canvas_config.width_inches,
            height_inches=canvas_config.height_inches,
            description=canvas_config.description
        )
        
        db.add(new_canvas_config)
        db.commit()
        db.refresh(new_canvas_config)
        
        return new_canvas_config
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating canvas config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create canvas configuration")

@app.put('/api/canvas-configs/{config_id}', response_model=CanvasConfigOut)
def update_canvas_config(config_id: int, canvas_config: CanvasConfigUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update an existing canvas configuration."""
    try:
        existing_config = db.query(CanvasConfig).filter(
            CanvasConfig.id == config_id,
            CanvasConfig.user_id == current_user.id
        ).first()
        
        if not existing_config:
            raise HTTPException(status_code=404, detail="Canvas configuration not found")
        
        # Update fields if provided
        if canvas_config.template_name is not None:
            existing_config.template_name = canvas_config.template_name
        if canvas_config.width_inches is not None:
            existing_config.width_inches = canvas_config.width_inches
        if canvas_config.height_inches is not None:
            existing_config.height_inches = canvas_config.height_inches
        if canvas_config.description is not None:
            existing_config.description = canvas_config.description
        if canvas_config.is_active is not None:
            existing_config.is_active = canvas_config.is_active
        
        db.commit()
        db.refresh(existing_config)
        
        return existing_config
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating canvas config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update canvas configuration")

@app.delete('/api/canvas-configs/{config_id}')
def delete_canvas_config(config_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a canvas configuration (soft delete by setting is_active to False)."""
    try:
        canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.id == config_id,
            CanvasConfig.user_id == current_user.id
        ).first()
        
        if not canvas_config:
            raise HTTPException(status_code=404, detail="Canvas configuration not found")
        
        canvas_config.is_active = False
        db.commit()
        
        return {'success': True, 'message': 'Canvas configuration deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting canvas config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete canvas configuration")

# --- Size Configuration API Endpoints ---
@app.get('/api/size-configs', response_model=List[SizeConfigOut])
def list_size_configs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all size configurations for the current user."""
    try:
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.user_id == current_user.id,
            SizeConfig.is_active == True
        ).all()
        return size_configs
    except Exception as e:
        print(f"Error listing size configs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list size configurations")

@app.get('/api/size-configs/{config_id}', response_model=SizeConfigOut)
def get_size_config(config_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific size configuration by ID."""
    try:
        size_config = db.query(SizeConfig).filter(
            SizeConfig.id == config_id,
            SizeConfig.user_id == current_user.id
        ).first()
        
        if not size_config:
            raise HTTPException(status_code=404, detail="Size configuration not found")
        
        return size_config
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting size config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get size configuration")

@app.post('/api/size-configs', response_model=SizeConfigOut)
def create_size_config(size_config: SizeConfigCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new size configuration."""
    try:
        # Check if template and size combination already exists for this user
        existing_config = db.query(SizeConfig).filter(
            SizeConfig.user_id == current_user.id,
            SizeConfig.template_name == size_config.template_name,
            SizeConfig.size_name == size_config.size_name,
            SizeConfig.is_active == True
        ).first()
        
        if existing_config:
            raise HTTPException(status_code=400, detail="Size configuration already exists for this template and size")
        
        new_size_config = SizeConfig(
            user_id=current_user.id,
            template_name=size_config.template_name,
            size_name=size_config.size_name,
            width_inches=size_config.width_inches,
            height_inches=size_config.height_inches,
            description=size_config.description
        )
        
        db.add(new_size_config)
        db.commit()
        db.refresh(new_size_config)
        
        return new_size_config
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating size config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create size configuration")

@app.put('/api/size-configs/{config_id}', response_model=SizeConfigOut)
def update_size_config(config_id: int, size_config: SizeConfigUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update an existing size configuration."""
    try:
        existing_config = db.query(SizeConfig).filter(
            SizeConfig.id == config_id,
            SizeConfig.user_id == current_user.id
        ).first()
        
        if not existing_config:
            raise HTTPException(status_code=404, detail="Size configuration not found")
        
        # Update fields if provided
        if size_config.template_name is not None:
            existing_config.template_name = size_config.template_name
        if size_config.size_name is not None:
            existing_config.size_name = size_config.size_name
        if size_config.width_inches is not None:
            existing_config.width_inches = size_config.width_inches
        if size_config.height_inches is not None:
            existing_config.height_inches = size_config.height_inches
        if size_config.description is not None:
            existing_config.description = size_config.description
        if size_config.is_active is not None:
            existing_config.is_active = size_config.is_active
        
        db.commit()
        db.refresh(existing_config)
        
        return existing_config
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating size config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update size configuration")

@app.delete('/api/size-configs/{config_id}')
def delete_size_config(config_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a size configuration (soft delete by setting is_active to False)."""
    try:
        size_config = db.query(SizeConfig).filter(
            SizeConfig.id == config_id,
            SizeConfig.user_id == current_user.id
        ).first()
        
        if not size_config:
            raise HTTPException(status_code=404, detail="Size configuration not found")
        
        size_config.is_active = False
        db.commit()
        
        return {'success': True, 'message': 'Size configuration deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting size config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete size configuration")

# --- Get Canvas and Size Configurations for Resizing ---
@app.get('/api/resizing-configs/{template_name}')
def get_resizing_configs(template_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get canvas and size configurations for a specific template name, formatted for resizing.py."""
    try:
        # Get canvas configuration
        canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.user_id == current_user.id,
            CanvasConfig.template_name == template_name,
            CanvasConfig.is_active == True
        ).first()
        
        # Get size configurations
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.user_id == current_user.id,
            SizeConfig.template_name == template_name,
            SizeConfig.is_active == True
        ).all()
        
        # Format for resizing.py compatibility
        canvas_data = {}
        if canvas_config:
            canvas_data = {
                'width': canvas_config.width_inches,
                'height': canvas_config.height_inches
            }
        
        sizing_data = {}
        for size_config in size_configs:
            if size_config.size_name:
                sizing_data[size_config.size_name] = {
                    'width': size_config.width_inches,
                    'height': size_config.height_inches
                }
            else:
                # For templates without size names, use template name as key
                sizing_data[template_name] = {
                    'width': size_config.width_inches,
                    'height': size_config.height_inches
                }
        
        return {
            'canvas': canvas_data,
            'sizing': sizing_data
        }
    except Exception as e:
        print(f"Error getting resizing configs for {template_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get resizing configurations")


@app.get("/")
async def serve_frontend():
    """Serve the React frontend."""
    # Try production build first (from server/static)
    index_path = os.path.join(project_root, 'server', 'static', 'index.html')
    
    if not os.path.exists(index_path):
        # Fallback to frontend build directory
        index_path = os.path.join(frontend_build_path, 'index.html')
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Fallback if React build doesn't exist
        return {"message": ERROR_MESSAGES['frontend_not_built']}

@app.get("/{full_path:path}")
async def serve_frontend_routes(full_path: str):
    """Serve React routes for client-side routing."""
    # Don't serve index.html for API routes
    if full_path.startswith('api/') or full_path.startswith('oauth/'):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Try production build first (from server/static)
    index_path = os.path.join(project_root, 'server', 'static', 'index.html')
    
    if not os.path.exists(index_path):
        # Fallback to frontend build directory
        index_path = os.path.join(frontend_build_path, 'index.html')
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": ERROR_MESSAGES['frontend_not_built']}
