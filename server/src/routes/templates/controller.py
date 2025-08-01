from fastapi import APIRouter, status, Depends, HTTPException
from uuid import UUID
from typing import List

from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.utils.etsy_api_engine import EtsyAPI
from . import model
from . import service

router = APIRouter(
    prefix="/settings",
    tags=["Settings", "EtsyProductTemplate"]
)

@router.post('/product-template', response_model=model.EtsyProductTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_product_template(product_template: model.EtsyProductTemplateCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.create_etsy_product_template(product_template, user_id, db)

@router.get('/product-template', response_model=List[model.EtsyProductTemplateResponse])
async def get_all_product_templates(current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.get_etsy_product_templates(user_id, db)

@router.get('/product-template/taxonomies', response_model=List[dict])
async def get_etsy_taxonomies(current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    etsy_api = EtsyAPI(user_id, db)
    taxonomies = etsy_api.fetch_all_taxonomies()
    return taxonomies

@router.get('/product-template/shop-sections', response_model=List[dict])
async def get_etsy_shop_sections(current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    etsy_api = EtsyAPI(user_id, db)
    shop_sections = etsy_api.fetch_all_shop_sections()
    return shop_sections

@router.get('/product-template/{product_template_id}', response_model=model.EtsyProductTemplateResponse)
async def get_product_template_by_id(product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.get_etsy_product_template_by_id(product_template_id, user_id, db)

@router.put('/product-template/{product_template_id}', response_model=model.EtsyProductTemplateResponse)
async def update_product_template_by_id(product_template: model.EtsyProductTemplateUpdate, product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.update_etsy_product_template(product_template, user_id, product_template_id, db)

@router.delete('/product-template/{product_template_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_template_by_id(product_template_id: UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.delete_etsy_product_template(user_id, product_template_id, db)