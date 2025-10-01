import os
import hmac
import hashlib
import secrets
import base64
from typing import Optional
from urllib.parse import urlencode, parse_qs, urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.entities.shopify_store import ShopifyStore
from server.src.entities.user import User
from . import model
from .service import ShopifyService
from .template_service import ShopifyTemplateProductService
from .analytics_service import ShopifyAnalyticsService
import requests
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import File, UploadFile, Form

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/shopify',
    tags=['shopify']
)

# Shopify OAuth configuration
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_SECRET = os.getenv('SHOPIFY_API_SECRET')

# Determine redirect URI based on environment
# Railway sets RAILWAY_PUBLIC_DOMAIN and RAILWAY_ENVIRONMENT_NAME
is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') or os.getenv('RAILWAY_PUBLIC_DOMAIN')
backend_url = os.getenv('BACKEND_URL') or os.getenv('RAILWAY_PUBLIC_DOMAIN')

if is_railway and backend_url:
    # Production on Railway
    if not backend_url.startswith('http'):
        backend_url = f"https://{backend_url}"
    default_redirect_uri = f"{backend_url}/api/shopify/callback"
else:
    # Local development
    default_redirect_uri = 'http://localhost:3003/api/shopify/callback'

SHOPIFY_REDIRECT_URI = os.getenv('SHOPIFY_REDIRECT_URI', default_redirect_uri)
SHOPIFY_SCOPES = os.getenv('SHOPIFY_SCOPES', 'read_products,write_products,read_orders')

# Log configuration on startup
logger.info(f"🔧 Shopify OAuth Configuration:")
logger.info(f"   Environment: {'Railway Production' if is_railway else 'Local Development'}")
logger.info(f"   Redirect URI: {SHOPIFY_REDIRECT_URI}")
logger.info(f"   API Key configured: {'✅ Yes' if SHOPIFY_API_KEY else '❌ No'}")
logger.info(f"   API Secret configured: {'✅ Yes' if SHOPIFY_API_SECRET else '❌ No'}")
logger.info(f"   Scopes: {SHOPIFY_SCOPES}")

# OAuth state storage (in production, use Redis or database)
oauth_states = {}

class ShopifyOAuthError(Exception):
    pass

def verify_shopify_hmac(query_string: str, hmac_header: str) -> bool:
    """Verify HMAC signature from Shopify"""
    if not SHOPIFY_API_SECRET:
        raise ShopifyOAuthError("SHOPIFY_API_SECRET not configured")

    # Remove hmac and signature from query string for verification
    query_params = parse_qs(query_string)
    if 'hmac' in query_params:
        del query_params['hmac']
    if 'signature' in query_params:
        del query_params['signature']

    # Sort parameters and create query string
    sorted_params = sorted(query_params.items())
    query_string_for_verification = '&'.join([f"{k}={'&'.join(v)}" for k, v in sorted_params])

    # Calculate HMAC
    calculated_hmac = hmac.new(
        SHOPIFY_API_SECRET.encode('utf-8'),
        query_string_for_verification.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(calculated_hmac, hmac_header)

def verify_shopify_webhook_hmac(body: bytes, hmac_header: str) -> bool:
    """Verify HMAC signature for Shopify webhooks"""
    if not SHOPIFY_API_SECRET:
        raise ShopifyOAuthError("SHOPIFY_API_SECRET not configured")

    calculated_hmac = base64.b64encode(
        hmac.new(
            SHOPIFY_API_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    return hmac.compare_digest(calculated_hmac, hmac_header)

def build_oauth_url(shop_domain: str, state: str) -> str:
    """Build Shopify OAuth authorization URL"""
    if not SHOPIFY_API_KEY:
        raise ShopifyOAuthError("SHOPIFY_API_KEY not configured")

    # Ensure shop domain has .myshopify.com suffix
    if not shop_domain.endswith('.myshopify.com'):
        shop_domain = f"{shop_domain}.myshopify.com"

    params = {
        'client_id': SHOPIFY_API_KEY,
        'scope': SHOPIFY_SCOPES,
        'redirect_uri': SHOPIFY_REDIRECT_URI,
        'state': state,
        'response_type': 'code'
    }

    return f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"

def exchange_code_for_token(shop_domain: str, code: str) -> dict:
    """Exchange authorization code for access token"""
    if not SHOPIFY_API_KEY or not SHOPIFY_API_SECRET:
        raise ShopifyOAuthError("Shopify API credentials not configured")

    # Ensure shop domain has .myshopify.com suffix
    if not shop_domain.endswith('.myshopify.com'):
        shop_domain = f"{shop_domain}.myshopify.com"

    token_url = f"https://{shop_domain}/admin/oauth/access_token"

    payload = {
        'client_id': SHOPIFY_API_KEY,
        'client_secret': SHOPIFY_API_SECRET,
        'code': code
    }

    try:
        response = requests.post(token_url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to exchange code for token: {e}")
        raise ShopifyOAuthError(f"Failed to exchange code for token: {e}")

def get_shop_info(shop_domain: str, access_token: str) -> dict:
    """Get shop information from Shopify API"""
    if not shop_domain.endswith('.myshopify.com'):
        shop_domain = f"{shop_domain}.myshopify.com"

    url = f"https://{shop_domain}/admin/api/2023-10/shop.json"
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to get shop info: {e}")
        raise ShopifyOAuthError(f"Failed to get shop info: {e}")

@router.post("/connect", response_model=model.ShopifyOAuthInitResponse)
async def initiate_shopify_oauth(
    request: model.ShopifyOAuthInitRequest,
    current_user: CurrentUser
):
    """Initiate Shopify OAuth flow"""
    try:
        # Check if Shopify credentials are configured
        if not SHOPIFY_API_KEY or not SHOPIFY_API_SECRET:
            logger.error("❌ Shopify API credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Shopify integration is not configured. Please contact the administrator to set up SHOPIFY_API_KEY and SHOPIFY_API_SECRET."
            )

        # Debug logging
        logger.info(f"🔗 Shopify OAuth Initiation")
        logger.info(f"   User: {current_user.get_uuid()}")
        logger.info(f"   Received shop_domain: {request.shop_domain!r}")
        logger.info(f"   Redirect URI: {SHOPIFY_REDIRECT_URI}")

        # Validate shop_domain is not empty
        if not request.shop_domain or not request.shop_domain.strip():
            logger.error(f"Empty shop_domain received: {request.shop_domain!r}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop domain is required and cannot be empty"
            )

        # Clean the shop domain
        clean_domain = request.shop_domain.strip()
        logger.info(f"   Cleaned shop_domain: {clean_domain!r}")

        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state with user ID (in production, use Redis or database)
        oauth_states[state] = {
            'user_id': str(current_user.get_uuid()),
            'shop_domain': clean_domain
        }

        # Build OAuth URL
        authorization_url = build_oauth_url(clean_domain, state)

        logger.info(f"✅ Generated OAuth URL: {authorization_url}")
        logger.info(f"   State stored for user {current_user.get_uuid()}")

        return model.ShopifyOAuthInitResponse(
            authorization_url=authorization_url,
            state=state
        )

    except HTTPException:
        raise
    except ShopifyOAuthError as e:
        logger.error(f"Shopify OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Shopify OAuth initiation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Shopify OAuth"
        )

@router.get("/callback")
async def shopify_oauth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Shopify OAuth callback"""
    try:
        logger.info(f"🔗 Shopify OAuth Callback received")
        logger.info(f"   Full URL: {request.url}")

        # Get query parameters
        query_params = dict(request.query_params)
        code = query_params.get('code')
        state = query_params.get('state')
        shop = query_params.get('shop')
        hmac_param = query_params.get('hmac')

        logger.info(f"   Parameters: code={'✅ Present' if code else '❌ Missing'}, state={'✅ Present' if state else '❌ Missing'}, shop={shop if shop else '❌ Missing'}")

        if not code or not state or not shop:
            logger.error(f"❌ Missing required OAuth parameters")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters (code, state, or shop)"
            )

        # Verify state parameter
        if state not in oauth_states:
            logger.error(f"❌ Invalid or expired state parameter: {state}")
            logger.error(f"   Available states: {list(oauth_states.keys())}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter. Please try connecting again."
            )

        oauth_data = oauth_states[state]
        user_id = oauth_data['user_id']
        logger.info(f"   User ID from state: {user_id}")

        # Verify HMAC (optional but recommended)
        if hmac_param:
            query_string = str(request.url.query)
            if not verify_shopify_hmac(query_string, hmac_param):
                logger.warning(f"HMAC verification failed for Shopify callback")
                # Don't fail the request, but log the warning

        # Exchange code for access token
        logger.info(f"   Exchanging code for access token...")
        token_data = exchange_code_for_token(shop, code)
        access_token = token_data.get('access_token')

        if not access_token:
            logger.error(f"❌ Failed to obtain access token from Shopify")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token from Shopify"
            )

        logger.info(f"   ✅ Access token obtained")

        # Get shop information
        logger.info(f"   Fetching shop information...")
        shop_info = get_shop_info(shop, access_token)
        shop_data = shop_info.get('shop', {})
        logger.info(f"   ✅ Shop info retrieved: {shop_data.get('name', shop)}")

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if user already has this specific Shopify store connected
        existing_store = db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.shop_domain == shop
        ).first()

        if existing_store:
            # Update existing store
            existing_store.shop_name = shop_data.get('name', shop)
            existing_store.access_token = access_token
            existing_store.is_active = True
            store = existing_store
        else:
            # Create new store record
            store = ShopifyStore(
                user_id=user_id,
                shop_domain=shop,
                shop_name=shop_data.get('name', shop),
                access_token=access_token,
                is_active=True
            )
            db.add(store)

        db.commit()
        db.refresh(store)

        # Clean up state
        del oauth_states[state]

        logger.info(f"✅ Successfully connected Shopify store {shop} for user {user_id}")
        logger.info(f"   Store ID: {store.id}")
        logger.info(f"   Shop Name: {store.shop_name}")

        # Return a redirect response to frontend success page
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        redirect_url = f"{frontend_url}/shopify/success"
        logger.info(f"   Redirecting to: {redirect_url}")

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except ShopifyOAuthError as e:
        logger.error(f"Shopify OAuth error in callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Shopify OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete Shopify OAuth"
        )

@router.get("/stores", response_model=model.ShopifyStoresListResponse)
async def get_shopify_stores(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get all connected Shopify stores for current user"""
    try:
        user_id = current_user.get_uuid()

        stores = db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.is_active == True
        ).all()

        store_responses = [model.ShopifyStoreResponse.from_orm(store) for store in stores]

        return model.ShopifyStoresListResponse(
            stores=store_responses,
            total=len(store_responses)
        )

    except Exception as e:
        logger.error(f"Error getting Shopify stores for user {current_user.get_uuid()}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Shopify store information"
        )

@router.get("/store", response_model=Optional[model.ShopifyStoreResponse])
async def get_shopify_store(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get first connected Shopify store for current user (legacy endpoint)"""
    try:
        user_id = current_user.get_uuid()

        store = db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.is_active == True
        ).first()

        if not store:
            return None

        return model.ShopifyStoreResponse.from_orm(store)

    except Exception as e:
        logger.error(f"Error getting Shopify store for user {current_user.get_uuid()}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Shopify store information"
        )

@router.delete("/disconnect")
async def disconnect_shopify_store(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Disconnect Shopify store for current user"""
    try:
        user_id = current_user.get_uuid()

        store = db.query(ShopifyStore).filter(ShopifyStore.user_id == user_id).first()

        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Shopify store connected"
            )

        # Mark as inactive instead of deleting
        store.is_active = False
        db.commit()

        logger.info(f"Disconnected Shopify store for user {user_id}")

        return {"success": True, "message": "Shopify store disconnected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting Shopify store for user {current_user.get_uuid()}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Shopify store"
        )

# Additional API endpoints for Shopify operations

@router.get("/orders")
async def get_orders(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    since_time: Optional[str] = None,
    limit: int = 250,
    status: str = "any"
):
    """Get orders from connected Shopify store"""
    service = ShopifyService(db)

    since_datetime = None
    if since_time:
        try:
            since_datetime = datetime.fromisoformat(since_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid datetime format. Use ISO format (e.g., 2023-01-01T00:00:00Z)"
            )

    orders = service.get_orders(
        user_id=current_user.get_uuid(),
        since_time=since_datetime,
        limit=limit,
        status=status
    )

    return {"orders": orders, "count": len(orders)}

@router.get("/products")
async def get_products(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = 250,
    published_status: str = "published"
):
    """Get products from connected Shopify store"""
    service = ShopifyService(db)

    products = service.get_products(
        user_id=current_user.get_uuid(),
        limit=limit,
        published_status=published_status
    )

    return {"products": products, "count": len(products)}

@router.get("/products/{product_id}")
async def get_product_by_id(
    product_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID"""
    service = ShopifyService(db)

    product = service.get_product_by_id(
        user_id=current_user.get_uuid(),
        product_id=product_id
    )

    return {"product": product}

@router.get("/orders/{order_id}")
async def get_order_by_id(
    order_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific order by ID"""
    service = ShopifyService(db)

    order = service.get_order_by_id(
        user_id=current_user.get_uuid(),
        order_id=order_id
    )

    return {"order": order}

@router.post("/products")
async def create_product(
    product_data: dict,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new product in Shopify store"""
    service = ShopifyService(db)

    product = service.create_product(
        user_id=current_user.get_uuid(),
        product_data=product_data
    )

    return {"product": product, "message": "Product created successfully"}

@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: dict,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update an existing product in Shopify store"""
    service = ShopifyService(db)

    product = service.update_product(
        user_id=current_user.get_uuid(),
        product_id=product_id,
        product_data=product_data
    )

    return {"product": product, "message": "Product updated successfully"}

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a product from Shopify store"""
    service = ShopifyService(db)

    success = service.delete_product(
        user_id=current_user.get_uuid(),
        product_id=product_id
    )

    return {"success": success, "message": "Product deleted successfully"}

@router.post("/products/{product_id}/images")
async def upload_product_image(
    product_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    position: Optional[int] = Form(None)
):
    """Upload an image to a product"""
    # Validate file type
    if not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    service = ShopifyService(db)

    uploaded_image = service.upload_product_image(
        user_id=current_user.get_uuid(),
        product_id=product_id,
        image_file=image,
        alt_text=alt_text,
        position=position
    )

    return {"image": uploaded_image, "message": "Image uploaded successfully"}

@router.get("/config")
async def get_shopify_config():
    """Get current Shopify OAuth configuration (for debugging)"""
    return {
        "environment": "Railway Production" if is_railway else "Local Development",
        "redirect_uri": SHOPIFY_REDIRECT_URI,
        "frontend_url": os.getenv('FRONTEND_URL', 'http://localhost:3000'),
        "api_key_configured": bool(SHOPIFY_API_KEY),
        "api_secret_configured": bool(SHOPIFY_API_SECRET),
        "scopes": SHOPIFY_SCOPES,
        "backend_url": backend_url if is_railway else "localhost:3003"
    }

@router.get("/test-connection")
async def test_shopify_connection(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Test connection to Shopify store"""
    service = ShopifyService(db)

    shop_info = service.test_connection(current_user.get_uuid())

    return {
        "connected": True,
        "shop": shop_info,
        "message": "Successfully connected to Shopify store"
    }

@router.post("/webhooks/verify")
async def verify_webhook(
    request: Request
):
    """Verify a Shopify webhook signature"""
    headers = dict(request.headers)
    body = await request.body()

    is_valid = ShopifyService.verify_webhook_signature(headers, body)

    return {
        "valid": is_valid,
        "message": "Webhook signature is valid" if is_valid else "Webhook signature is invalid"
    }

# Template-based product creation endpoints

@router.get("/templates")
async def get_templates(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get available product templates"""
    template_service = ShopifyTemplateProductService(db)
    templates = template_service.get_available_templates(current_user.get_uuid())
    return {"templates": templates}

@router.get("/templates/{template_id}/mockups")
async def get_template_mockups(
    template_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get mockup configurations for a template"""
    template_service = ShopifyTemplateProductService(db)
    mockups = template_service.get_template_mockups(
        template_id=UUID(template_id),
        user_id=current_user.get_uuid()
    )
    return {"mockups": mockups}

@router.post("/templates/{template_id}/preview")
async def generate_mockup_preview(
    template_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    design_files: List[UploadFile] = File(...)
):
    """Generate mockup preview for template and design files"""
    if not design_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one design file is required"
        )

    template_service = ShopifyTemplateProductService(db)
    preview = template_service.generate_mockup_preview(
        template_id=UUID(template_id),
        design_files=design_files,
        user_id=current_user.get_uuid()
    )
    return preview

@router.post("/products/from-template")
async def create_product_from_template(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    template_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    vendor: str = Form("Custom Design Store"),
    tags: str = Form(""),
    variants: str = Form("[]"),  # JSON string of variants
    design_files: List[UploadFile] = File(...)
):
    """Create a Shopify product using a template and design files"""
    if not design_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one design file is required"
        )

    # Parse variants JSON
    try:
        import json
        variants_data = json.loads(variants) if variants != "[]" else []
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid variants JSON format"
        )

    # Prepare product details
    product_details = {
        'title': title,
        'description': description,
        'price': price,
        'vendor': vendor,
        'tags': tags,
        'variants': variants_data
    }

    template_service = ShopifyTemplateProductService(db)
    result = template_service.create_shopify_product_from_template(
        user_id=current_user.get_uuid(),
        template_id=UUID(template_id),
        design_files=design_files,
        product_details=product_details
    )

    return {
        "success": True,
        "message": "Product created successfully",
        "product": result
    }

@router.get("/products/my-products")
async def get_my_shopify_products(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get all Shopify products created by the current user"""
    template_service = ShopifyTemplateProductService(db)
    products = template_service.get_user_shopify_products(current_user.get_uuid())
    return {"products": products}

# Analytics endpoints

@router.get("/orders/stats")
async def get_order_stats(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "day"
):
    """Get order statistics grouped by time period"""
    analytics_service = ShopifyAnalyticsService(db)

    # Parse date parameters
    start_datetime = None
    end_datetime = None

    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (e.g., 2023-01-01T00:00:00Z)"
            )

    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (e.g., 2023-01-01T00:00:00Z)"
            )

    # Validate group_by parameter
    if group_by not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="group_by must be one of: day, week, month"
        )

    stats = analytics_service.get_order_stats(
        user_id=current_user.get_uuid(),
        start_date=start_datetime,
        end_date=end_datetime,
        group_by=group_by
    )

    return stats

@router.get("/orders/top-products")
async def get_top_products(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10
):
    """Get top-selling products ranked by sales"""
    analytics_service = ShopifyAnalyticsService(db)

    # Parse date parameters
    start_datetime = None
    end_datetime = None

    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (e.g., 2023-01-01T00:00:00Z)"
            )

    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (e.g., 2023-01-01T00:00:00Z)"
            )

    # Validate limit parameter
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100"
        )

    top_products = analytics_service.get_top_products(
        user_id=current_user.get_uuid(),
        start_date=start_datetime,
        end_date=end_datetime,
        limit=limit
    )

    return top_products

@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics summary for dashboard"""
    analytics_service = ShopifyAnalyticsService(db)

    summary = analytics_service.get_order_analytics_summary(
        user_id=current_user.get_uuid()
    )

    return summary