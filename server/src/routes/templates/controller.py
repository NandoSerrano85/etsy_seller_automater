from fastapi import APIRouter, status, Depends, HTTPException
from uuid import UUID
from typing import List

from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.utils.etsy_api_engine import EtsyAPI
from . import model
from . import service
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix="/settings",
    tags=["Settings", "EtsyProductTemplate"]
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="templates-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

@router.post('/product-template', response_model=model.EtsyProductTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_product_template(product_template: model.EtsyProductTemplateCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Create product template (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def create_product_template_threaded():
        return service.create_etsy_product_template(product_template, user_id, db)

    return await create_product_template_threaded()

@router.get('/product-template', response_model=List[model.EtsyProductTemplateResponse])
async def get_all_product_templates(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get all product templates (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_all_product_templates_threaded():
        return service.get_etsy_product_templates(user_id, db)

    return await get_all_product_templates_threaded()

@router.get('/product-template/taxonomies', response_model=List[dict])
async def get_etsy_taxonomies(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get Etsy taxonomies (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_etsy_taxonomies_threaded():
        etsy_api = EtsyAPI(user_id, db)
        return etsy_api.fetch_all_taxonomies()

    return await get_etsy_taxonomies_threaded()

@router.get('/product-template/shop-sections', response_model=List[dict])
async def get_etsy_shop_sections(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get Etsy shop sections (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_etsy_shop_sections_threaded():
        etsy_api = EtsyAPI(user_id, db)
        return etsy_api.fetch_all_shop_sections()

    return await get_etsy_shop_sections_threaded()

@router.get('/product-template/{product_template_id}', response_model=model.EtsyProductTemplateResponse)
async def get_product_template_by_id(product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get product template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_product_template_by_id_threaded():
        return service.get_etsy_product_template_by_id(product_template_id, user_id, db)

    return await get_product_template_by_id_threaded()

@router.put('/product-template/{product_template_id}', response_model=model.EtsyProductTemplateResponse)
async def update_product_template_by_id(product_template: model.EtsyProductTemplateUpdate, product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Update product template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def update_product_template_by_id_threaded():
        return service.update_etsy_product_template(product_template, user_id, product_template_id, db)

    return await update_product_template_by_id_threaded()

@router.delete('/product-template/{product_template_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_template_by_id(product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Delete product template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def delete_product_template_by_id_threaded():
        return service.delete_etsy_product_template(user_id, product_template_id, db)

    await delete_product_template_by_id_threaded()

# Shopify Product Template Endpoints
@router.post('/shopify-product-template', response_model=model.ShopifyProductTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_shopify_product_template(product_template: model.ShopifyProductTemplateCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Create Shopify product template (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def create_shopify_product_template_threaded():
        return service.create_shopify_product_template(product_template, user_id, db)

    return await create_shopify_product_template_threaded()

@router.get('/shopify-product-template', response_model=List[model.ShopifyProductTemplateResponse])
async def get_all_shopify_product_templates(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get all Shopify product templates (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_all_shopify_product_templates_threaded():
        return service.get_shopify_product_templates(user_id, db)

    return await get_all_shopify_product_templates_threaded()

@router.get('/shopify-product-template/{product_template_id}', response_model=model.ShopifyProductTemplateResponse)
async def get_shopify_product_template_by_id(product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get Shopify product template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_shopify_product_template_by_id_threaded():
        return service.get_shopify_product_template_by_id(product_template_id, user_id, db)

    return await get_shopify_product_template_by_id_threaded()

@router.put('/shopify-product-template/{product_template_id}', response_model=model.ShopifyProductTemplateResponse)
async def update_shopify_product_template_by_id(product_template: model.ShopifyProductTemplateUpdate, product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Update Shopify product template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def update_shopify_product_template_by_id_threaded():
        return service.update_shopify_product_template(product_template, user_id, product_template_id, db)

    return await update_shopify_product_template_by_id_threaded()

@router.delete('/shopify-product-template/{product_template_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopify_product_template_by_id(product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Delete Shopify product template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def delete_shopify_product_template_by_id_threaded():
        return service.delete_shopify_product_template(user_id, product_template_id, db)

    await delete_shopify_product_template_by_id_threaded()