from fastapi import FastAPI, APIRouter, Request, HTTPException, UploadFile, File, Form, Depends, Security, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, requests, time, json, glob, tempfile, shutil, random
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pprint import pprint
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session

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
from server.api.models import Base, User, OAuthToken, EtsyTemplate, get_db

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
    materials: Optional[str] = None
    shop_section_id: Optional[int] = None
    quantity: Optional[int] = None
    tags: Optional[str] = None
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
        orm_mode = True

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
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload['user_id']).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Create the main FastAPI app
app = FastAPI(title="Etsy Seller Automaker", version="1.0.0")

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
        local_images_response = await get_local_images()
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
async def create_masks(mask_data: MaskData, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
        
        # Save mask data to database
        mask_data_obj = save_mask_data_to_db(
            db=db,
            user_id=current_user.id,
            template_name=mask_data.imageType,
            masks_data=masks_dict
        )
        
        return {
            "success": True,
            "message": f"Successfully saved {len(masks_dict)} masks for {mask_data.imageType}",
            "masks_count": len(masks_dict),
            "template_name": mask_data.imageType,
            "mask_data_id": mask_data_obj.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving masks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save masks: {str(e)}")

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
        from server.engine.mask_db_utils import load_mask_data_from_db
        
        masks, points_list, starting_name = load_mask_data_from_db(db, current_user.id, template_name)
        
        return {
            "success": True,
            "template_name": template_name,
            "masks_count": len(masks),
            "points_count": len(points_list),
            "starting_name": starting_name,
            "masks": masks,
            "points": points_list
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
    
    # Get the first available template for the user, or use default
    template = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id).first()
    template_name = template.name if template else "UVDTF 16oz"
    
    item_summary = etsy_api.fetch_open_orders_items(os.getenv('LOCAL_ROOT_PATH'), template_name)
    try:
        create_gang_sheets(
            item_summary[template_name] if template_name in item_summary else item_summary.get("UVDTF 16oz", {}),
            template_name,
            f"{os.getenv('LOCAL_ROOT_PATH')}/Printfiles/",
            item_summary["Total QTY"] if item_summary else 0
        )
    except Exception as e:
        print(f"Error creating gang sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create gang sheets: {str(e)}")
    return item_summary

@app.get('/api/local-images')
async def get_local_images(current_user: User = Depends(get_current_user)):
    """API endpoint to get list of local PNG images."""
    try:
        # Get user's templates to find available image directories
        db = next(get_db())
        templates = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id).all()
        
        all_images = []
        
        for template in templates:
            # Path to the template's images directory
            images_path = f"/Users/fserrano/Desktop/Desktop/NookTransfers/{template.name}/"
            
            if os.path.exists(images_path):
                # Get all PNG files for this template
                png_files = glob.glob(os.path.join(images_path, "*.png"))
                
                # Convert to relative paths for the frontend
                for file_path in png_files:
                    filename = os.path.basename(file_path)
                    all_images.append({
                        "filename": filename,
                        "path": f"/api/local-images/{filename}",
                        "full_path": file_path,
                        "template_name": template.name,
                        "template_title": template.template_title
                    })
        
        return {"images": all_images}
    except Exception as e:
        print(f"Error getting local images: {str(e)}")
        return {"images": [], "error": str(e)}

@app.get('/api/local-images/{filename}')
async def serve_local_image(filename: str):
    """API endpoint to serve local PNG images."""
    try:
        # Search for the image in all template directories
        base_path = "/Users/fserrano/Desktop/Desktop/NookTransfers/"
        
        # Look for the file in any subdirectory
        for root, dirs, files in os.walk(base_path):
            if filename in files:
                file_path = os.path.join(root, filename)
                return FileResponse(file_path, media_type="image/png")
        
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        print(f"Error serving image {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving image")

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
    try:
        # Path to the mockup images directory
        mockup_path = "/Users/fserrano/Desktop/Desktop/NookTransfers/Mockups/Cup Wraps/"
        if not os.path.exists(mockup_path):
            return {"images": [], "error": "Mockup images directory not found"}
        # Get all PNG and JPG files
        image_files = glob.glob(os.path.join(mockup_path, "*.png")) + glob.glob(os.path.join(mockup_path, "*.jpg"))
        images = []
        for file_path in image_files:
            filename = os.path.basename(file_path)
            images.append({
                "filename": filename,
                "path": f"/api/mockup-images/{filename}",
                "full_path": file_path
            })
        return {"images": images}
    except Exception as e:
        print(f"Error getting mockup images: {str(e)}")
        return {"images": [], "error": str(e)}

@app.get('/api/mockup-images/{filename}')
async def serve_mockup_image(filename: str):
    """API endpoint to serve local mockup images."""
    try:
        mockup_path = "/Users/fserrano/Desktop/Desktop/NookTransfers/Mockups/Cup Wraps/"
        file_path = os.path.join(mockup_path, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Mockup image not found")
        return FileResponse(file_path, media_type="image/png")
    except Exception as e:
        print(f"Error serving mockup image {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving mockup image")

@app.post('/api/upload-mockup')
async def upload_mockup(
    files: List[UploadFile] = File(...), 
    template_name: str = Form('UVDTF 16oz'),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        # Define the target directory for uploaded files
        target_dir = "/Users/fserrano/Desktop/Desktop/NookTransfers/Origin/16oz/"
        os.makedirs(target_dir, exist_ok=True)
        uploaded_file_paths = []
        for file in files:
            if file.filename:
                safe_filename = file.filename.replace('/', '_').replace('\\', '_')
                file_path = os.path.join(target_dir, safe_filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                uploaded_file_paths.append(file_path)
        result = process_uploaded_mockups(
            uploaded_file_paths, 
            "/Users/fserrano/Desktop/Desktop/NookTransfers/", 
            template_name,
            user_id=current_user.id,
            db=db
        )
        etsy_api = EtsyAPI()
        # Fetch the user's template by name
        template = db.query(EtsyTemplate).filter(EtsyTemplate.user_id == current_user.id, EtsyTemplate.name == template_name).first()
        if not template:
            return JSONResponse(status_code=400, content={"success": False, "error": f"No template named '{template_name}' found for this user."})
        # Parse materials and tags from string to list if needed
        materials = template.materials.split(',') if template.materials else []
        tags = template.tags.split(',') if template.tags else []
        for design, mockups in result.items():
            title = design.split(' ')[:2]
            listing_response = etsy_api.create_draft_listing(
                title=' '.join(title + [template.title]) if template.title else ' '.join(title),
                description=template.description,
                price=template.price,
                quantity=template.quantity,
                tags=tags,
                materials=materials)
            listing_id = listing_response["listing_id"]
            for mockup in random.sample(mockups, len(mockups)):
                etsy_api.upload_listing_image(listing_id, mockup)
        for filename in os.listdir(target_dir):
            file_path = os.path.join(target_dir, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Error deleting file {filename}: {e}")
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
        print(f"Error in upload-mockup: {str(e)}")
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

class UserLogin(BaseModel):
    email: str
    password: str

@app.post('/api/register')
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    normalized_email = user.email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=normalized_email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"success": True, "user_id": new_user.id}

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
        
        db_template = EtsyTemplate(
            user_id=current_user.id,
            name=template.name,
            title=template.title,
            description=template.description,
            who_made=template.who_made,
            when_made=template.when_made,
            taxonomy_id=template.taxonomy_id,
            price=template.price,
            materials=','.join(template.materials) if template.materials else None,
            shop_section_id=template.shop_section_id,
            quantity=template.quantity,
            tags=','.join(template.tags) if template.tags else None,
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
            if field in ['materials', 'tags'] and value is not None:
                setattr(db_template, field, ','.join(value))
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
            return_policy_id=0
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

# Example usage for a protected endpoint:
# @app.get('/api/protected')
# def protected_route(current_user: User = Depends(get_current_user)):
#     return {"message": f"Hello, {current_user.email}"}

