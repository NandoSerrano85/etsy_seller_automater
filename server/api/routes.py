from fastapi import FastAPI, APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, requests, time, json, glob, tempfile, shutil
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
from pprint import pprint

# Import OAuth logic from etsy_oath_token
from server.engine.etsy_api_engine import EtsyAPI
from server.engine.etsy_oath_token import get_oauth_variables, store_oauth_tokens
from server.engine.gangsheet_engine import create_gang_sheets

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
    DEFAULTS,
    ETSY_TEMPLATES
)

# Import mockup engine
from server.engine.mockup_engine import process_uploaded_mockups

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

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

@app.get('/api/top-sellers')
async def get_top_sellers(access_token: str, year: int = None):
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
async def get_shop_listings(access_token: str, limit: int = 50, offset: int = 0):
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

@app.get('/api/create-gang-sheets')
async def get_etsy_item_summary():
    """API endpoint to get item summary from Etsy."""
    etsy_api = EtsyAPI()
    item_summary = etsy_api.fetch_open_orders_items(os.getenv('LOCAL_ROOT_PATH'), "UVDTF 16oz")
    try:
        create_gang_sheets(
            item_summary["UVDTF 16oz"],
            "UVDTF 16oz",
            f"{os.getenv('LOCAL_ROOT_PATH')}/Printfiles/",
            item_summary["Total QTY"] if item_summary else 0
        )
    except Exception as e:
        print(f"Error creating gang sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create gang sheets: {str(e)}")
    return item_summary

@app.get('/api/local-images')
async def get_local_images():
    """API endpoint to get list of local PNG images."""
    try:
        # Path to the UVDTF 16oz images directory
        images_path = "/Users/fserrano/Desktop/Desktop/NookTransfers/UVDTF 16oz/"
        
        if not os.path.exists(images_path):
            return {"images": [], "error": "Images directory not found"}
        
        # Get all PNG files
        png_files = glob.glob(os.path.join(images_path, "*.png"))
        
        # Convert to relative paths for the frontend
        images = []
        for file_path in png_files:
            filename = os.path.basename(file_path)
            images.append({
                "filename": filename,
                "path": f"/api/local-images/{filename}",
                "full_path": file_path
            })
        
        return {"images": images}
    except Exception as e:
        print(f"Error getting local images: {str(e)}")
        return {"images": [], "error": str(e)}

@app.get('/api/local-images/{filename}')
async def serve_local_image(filename: str):
    """API endpoint to serve local PNG images."""
    try:
        # Path to the UVDTF 16oz images directory
        images_path = "/Users/fserrano/Desktop/Desktop/NookTransfers/UVDTF 16oz/"
        file_path = os.path.join(images_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(file_path, media_type="image/png")
    except Exception as e:
        print(f"Error serving image {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving image")

@app.get('/api/monthly-analytics')
async def get_monthly_analytics(access_token: str, year: int = None):
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
async def get_mockup_images():
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
async def upload_mockup(files: List[UploadFile] = File(...)):
    try:
        # Define the target directory for uploaded files
        target_dir = "/Users/fserrano/Desktop/Desktop/NookTransfers/Origin/16oz/"
        
        # Ensure the target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        uploaded_file_paths = []
        
        # Save uploaded files to the target directory
        for file in files:
            if file.filename:
                # Create a safe filename
                safe_filename = file.filename.replace('/', '_').replace('\\', '_')
                file_path = os.path.join(target_dir, safe_filename)
                
                # Save the uploaded file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                print(file_path)
                uploaded_file_paths.append(file_path)
                print(f"Saved uploaded file to: {file_path}")
        
        
        # Call the mockup_engine logic with the file paths
        result = process_uploaded_mockups(uploaded_file_paths, "/Users/fserrano/Desktop/Desktop/NookTransfers/")
        
        # Process the result and create Etsy listings
        etsy_api = EtsyAPI()
        
        for design, mockups in result.items():
            print(design)
            print(mockups)
            title = design.split(' ')[:2]
            listing_response = etsy_api.create_draft_listing(
                title=' '.join(title + [ETSY_TEMPLATES['UVDTF 16oz']['title']]), 
                description=ETSY_TEMPLATES['UVDTF 16oz']['description'], 
                price=ETSY_TEMPLATES['UVDTF 16oz']['price'], 
                quantity=ETSY_TEMPLATES['UVDTF 16oz']['quantity'], 
                tags=ETSY_TEMPLATES['UVDTF 16oz']['tags'], 
                materials=ETSY_TEMPLATES['UVDTF 16oz']['materials'])

            listing_id = listing_response["listing_id"]
            for mockup in mockups:
                etsy_api.upload_listing_image(listing_id, mockup)

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
async def get_orders(access_token: str):
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
            'was_shipped': 'false'  # Only get open/active orders
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