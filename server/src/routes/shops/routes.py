"""
Shop API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from server.src.database.core import get_db
from server.src.auth.dependencies import get_current_user
from server.src.entities.user import User
from server.src.routes.organizations.service import OrganizationService
from . import model
from .service import ShopService

router = APIRouter(prefix="/organizations/{org_id}/shops", tags=["shops"])

@router.post("/", response_model=model.ShopResponse)
def create_shop(
    org_id: UUID,
    shop_data: model.ShopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new shop connection"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    try:
        shop = ShopService.create_shop(
            db=db,
            org_id=org_id,
            shop_data=shop_data,
            user_id=current_user.id
        )
        return model.ShopResponse.model_validate(shop)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=model.ShopListResponse)
def get_shops(
    org_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of shops for organization"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    shops, total = ShopService.get_shops_by_org(db=db, org_id=org_id, skip=skip, limit=limit)
    
    return model.ShopListResponse(
        shops=[model.ShopResponse.model_validate(shop) for shop in shops],
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/{shop_id}", response_model=model.ShopResponse)
def get_shop(
    org_id: UUID,
    shop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shop by ID"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    shop = ShopService.get_shop_by_id(db=db, shop_id=shop_id)
    if not shop or shop.org_id != org_id:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return model.ShopResponse.model_validate(shop)

@router.put("/{shop_id}", response_model=model.ShopResponse)
def update_shop(
    org_id: UUID,
    shop_id: UUID,
    shop_data: model.ShopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update shop connection"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    shop = ShopService.get_shop_by_id(db=db, shop_id=shop_id)
    if not shop or shop.org_id != org_id:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    updated_shop = ShopService.update_shop(
        db=db,
        shop_id=shop_id,
        shop_data=shop_data,
        user_id=current_user.id
    )
    if not updated_shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return model.ShopResponse.model_validate(updated_shop)

@router.delete("/{shop_id}")
def delete_shop(
    org_id: UUID,
    shop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete shop connection"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    shop = ShopService.get_shop_by_id(db=db, shop_id=shop_id)
    if not shop or shop.org_id != org_id:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    success = ShopService.delete_shop(
        db=db,
        shop_id=shop_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return {"message": "Shop disconnected successfully"}

@router.post("/{shop_id}/sync")
def sync_shop(
    org_id: UUID,
    shop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger shop synchronization"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    shop = ShopService.get_shop_by_id(db=db, shop_id=shop_id)
    if not shop or shop.org_id != org_id:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Update last sync timestamp
    success = ShopService.update_last_sync(db=db, shop_id=shop_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update sync timestamp")
    
    # TODO: Trigger background sync job
    return {"message": "Shop sync initiated", "shop_id": shop_id}