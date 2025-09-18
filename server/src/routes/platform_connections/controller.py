from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.entities.platform_connection import PlatformConnection, PlatformType
from server.src.entities.etsy_store import EtsyStore
from server.src.entities.shopify_store import ShopifyStore
from . import model
from . import service

router = APIRouter(
    prefix='/api/platform-connections',
    tags=['platform-connections']
)

# Platform Connection Management
@router.get("/", response_model=model.PlatformConnectionListResponse)
async def get_platform_connections(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    platform: Optional[model.PlatformTypeEnum] = None
):
    """Get all platform connections for the current user"""
    connections = service.get_user_platform_connections(db, current_user.user_id, platform)
    return model.PlatformConnectionListResponse(
        connections=[model.PlatformConnectionResponse.model_validate(conn) for conn in connections],
        total=len(connections)
    )

@router.post("/", response_model=model.PlatformConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_platform_connection(
    connection_data: model.PlatformConnectionCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new platform connection"""
    connection = service.create_platform_connection(db, current_user.user_id, connection_data)
    return model.PlatformConnectionResponse.model_validate(connection)

@router.get("/{connection_id}", response_model=model.PlatformConnectionResponse)
async def get_platform_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific platform connection"""
    connection = service.get_platform_connection(db, connection_id, current_user.user_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Platform connection not found")
    return model.PlatformConnectionResponse.model_validate(connection)

@router.put("/{connection_id}", response_model=model.PlatformConnectionResponse)
async def update_platform_connection(
    connection_id: UUID,
    update_data: model.PlatformConnectionUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a platform connection"""
    connection = service.update_platform_connection(db, connection_id, current_user.user_id, update_data)
    if not connection:
        raise HTTPException(status_code=404, detail="Platform connection not found")
    return model.PlatformConnectionResponse.model_validate(connection)

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a platform connection"""
    success = service.delete_platform_connection(db, connection_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Platform connection not found")

@router.post("/{connection_id}/verify", response_model=model.ConnectionVerificationResponse)
async def verify_platform_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Verify that a platform connection is still valid"""
    result = await service.verify_platform_connection(db, connection_id, current_user.user_id)
    return result

# Etsy Store Management
@router.get("/etsy/stores", response_model=model.EtsyStoreListResponse)
async def get_etsy_stores(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get all Etsy stores for the current user"""
    stores = service.get_user_etsy_stores(db, current_user.user_id)
    return model.EtsyStoreListResponse(
        stores=[model.EtsyStoreResponse.model_validate(store) for store in stores],
        total=len(stores)
    )

@router.post("/etsy/stores", response_model=model.EtsyStoreResponse, status_code=status.HTTP_201_CREATED)
async def create_etsy_store(
    store_data: model.EtsyStoreCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new Etsy store"""
    store = service.create_etsy_store(db, current_user.user_id, store_data)
    return model.EtsyStoreResponse.model_validate(store)

@router.get("/etsy/stores/{store_id}", response_model=model.EtsyStoreResponse)
async def get_etsy_store(
    store_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific Etsy store"""
    store = service.get_etsy_store(db, store_id, current_user.user_id)
    if not store:
        raise HTTPException(status_code=404, detail="Etsy store not found")
    return model.EtsyStoreResponse.model_validate(store)

@router.put("/etsy/stores/{store_id}", response_model=model.EtsyStoreResponse)
async def update_etsy_store(
    store_id: UUID,
    update_data: model.EtsyStoreUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update an Etsy store"""
    store = service.update_etsy_store(db, store_id, current_user.user_id, update_data)
    if not store:
        raise HTTPException(status_code=404, detail="Etsy store not found")
    return model.EtsyStoreResponse.model_validate(store)

@router.delete("/etsy/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_etsy_store(
    store_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete an Etsy store"""
    success = service.delete_etsy_store(db, store_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Etsy store not found")

# Enhanced Shopify Store Management
@router.get("/shopify/stores", response_model=model.ShopifyStoreEnhancedListResponse)
async def get_enhanced_shopify_stores(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get all Shopify stores for the current user with enhanced information"""
    stores = service.get_user_shopify_stores_enhanced(db, current_user.user_id)
    return model.ShopifyStoreEnhancedListResponse(
        stores=[model.ShopifyStoreEnhancedResponse.model_validate(store) for store in stores],
        total=len(stores)
    )

@router.put("/shopify/stores/{store_id}", response_model=model.ShopifyStoreEnhancedResponse)
async def update_enhanced_shopify_store(
    store_id: UUID,
    update_data: model.ShopifyStoreEnhancedUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a Shopify store with enhanced information"""
    store = service.update_shopify_store_enhanced(db, store_id, current_user.user_id, update_data)
    if not store:
        raise HTTPException(status_code=404, detail="Shopify store not found")
    return model.ShopifyStoreEnhancedResponse.model_validate(store)

# Bulk operations
@router.post("/verify-all", response_model=model.BulkConnectionVerificationResponse)
async def verify_all_connections(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Verify all platform connections for the current user"""
    result = await service.verify_all_user_connections(db, current_user.user_id)
    return result

# Platform setup helpers
@router.post("/setup", response_model=model.PlatformSetupResponse)
async def setup_platform(
    setup_data: model.PlatformSetupRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Setup a new platform connection and store in one operation"""
    result = await service.setup_platform_connection(db, current_user.user_id, setup_data)
    return result