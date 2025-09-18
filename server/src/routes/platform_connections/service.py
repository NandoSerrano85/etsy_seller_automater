from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from server.src.entities.platform_connection import PlatformConnection, PlatformType, ConnectionType
from server.src.entities.etsy_store import EtsyStore
from server.src.entities.shopify_store import ShopifyStore
from server.src.entities.user import User
from . import model

import logging
logger = logging.getLogger(__name__)

# Platform Connection CRUD operations
def get_user_platform_connections(
    db: Session,
    user_id: UUID,
    platform: Optional[model.PlatformTypeEnum] = None
) -> List[PlatformConnection]:
    """Get all platform connections for a user, optionally filtered by platform"""
    query = db.query(PlatformConnection).filter(PlatformConnection.user_id == user_id)

    if platform:
        platform_enum = PlatformType(platform.value)
        query = query.filter(PlatformConnection.platform == platform_enum)

    return query.order_by(PlatformConnection.created_at.desc()).all()

def create_platform_connection(
    db: Session,
    user_id: UUID,
    connection_data: model.PlatformConnectionCreate
) -> PlatformConnection:
    """Create a new platform connection"""
    connection = PlatformConnection(
        user_id=user_id,
        platform=PlatformType(connection_data.platform.value),
        connection_type=ConnectionType(connection_data.connection_type.value),
        access_token=connection_data.access_token,
        refresh_token=connection_data.refresh_token,
        token_expires_at=connection_data.token_expires_at,
        auth_data=connection_data.auth_data,
        is_active=connection_data.is_active
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection

def get_platform_connection(
    db: Session,
    connection_id: UUID,
    user_id: UUID
) -> Optional[PlatformConnection]:
    """Get a specific platform connection by ID"""
    return db.query(PlatformConnection).filter(
        and_(
            PlatformConnection.id == connection_id,
            PlatformConnection.user_id == user_id
        )
    ).first()

def update_platform_connection(
    db: Session,
    connection_id: UUID,
    user_id: UUID,
    update_data: model.PlatformConnectionUpdate
) -> Optional[PlatformConnection]:
    """Update a platform connection"""
    connection = get_platform_connection(db, connection_id, user_id)
    if not connection:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(connection, field, value)

    db.commit()
    db.refresh(connection)
    return connection

def delete_platform_connection(
    db: Session,
    connection_id: UUID,
    user_id: UUID
) -> bool:
    """Delete a platform connection"""
    connection = get_platform_connection(db, connection_id, user_id)
    if not connection:
        return False

    # Also delete associated stores
    if connection.platform == PlatformType.ETSY:
        db.query(EtsyStore).filter(EtsyStore.connection_id == connection_id).delete()
    elif connection.platform == PlatformType.SHOPIFY:
        db.query(ShopifyStore).filter(ShopifyStore.connection_id == connection_id).delete()

    db.delete(connection)
    db.commit()
    return True

async def verify_platform_connection(
    db: Session,
    connection_id: UUID,
    user_id: UUID
) -> model.ConnectionVerificationResponse:
    """Verify that a platform connection is still valid"""
    connection = get_platform_connection(db, connection_id, user_id)
    if not connection:
        return model.ConnectionVerificationResponse(
            is_valid=False,
            platform=model.PlatformTypeEnum.ETSY,
            error_message="Connection not found"
        )

    try:
        # Check if token is expired
        if connection.is_token_expired():
            return model.ConnectionVerificationResponse(
                is_valid=False,
                platform=model.PlatformTypeEnum(connection.platform.value),
                last_verified_at=connection.last_verified_at,
                error_message="Access token is expired"
            )

        # TODO: Implement actual API verification based on platform
        # For now, just check if we have an access token
        is_valid = bool(connection.access_token and connection.is_active)

        if is_valid:
            # Update last verified timestamp
            connection.last_verified_at = datetime.now(timezone.utc)
            db.commit()

        return model.ConnectionVerificationResponse(
            is_valid=is_valid,
            platform=model.PlatformTypeEnum(connection.platform.value),
            last_verified_at=connection.last_verified_at,
            error_message=None if is_valid else "No valid access token"
        )

    except Exception as e:
        logger.error(f"Error verifying connection {connection_id}: {e}")
        return model.ConnectionVerificationResponse(
            is_valid=False,
            platform=model.PlatformTypeEnum(connection.platform.value),
            error_message=f"Verification failed: {str(e)}"
        )

# Etsy Store CRUD operations
def get_user_etsy_stores(db: Session, user_id: UUID) -> List[EtsyStore]:
    """Get all Etsy stores for a user"""
    return db.query(EtsyStore).filter(EtsyStore.user_id == user_id).order_by(EtsyStore.created_at.desc()).all()

def create_etsy_store(
    db: Session,
    user_id: UUID,
    store_data: model.EtsyStoreCreate
) -> EtsyStore:
    """Create a new Etsy store"""
    # Verify the connection belongs to the user and is for Etsy
    connection = get_platform_connection(db, store_data.connection_id, user_id)
    if not connection or connection.platform != PlatformType.ETSY:
        raise ValueError("Invalid Etsy connection")

    store = EtsyStore(
        user_id=user_id,
        connection_id=store_data.connection_id,
        etsy_shop_id=store_data.etsy_shop_id,
        shop_name=store_data.shop_name,
        shop_url=store_data.shop_url,
        currency_code=store_data.currency_code,
        country_code=store_data.country_code,
        language=store_data.language,
        is_active=store_data.is_active,
        is_vacation_mode=store_data.is_vacation_mode
    )

    db.add(store)
    db.commit()
    db.refresh(store)
    return store

def get_etsy_store(db: Session, store_id: UUID, user_id: UUID) -> Optional[EtsyStore]:
    """Get a specific Etsy store by ID"""
    return db.query(EtsyStore).filter(
        and_(
            EtsyStore.id == store_id,
            EtsyStore.user_id == user_id
        )
    ).first()

def update_etsy_store(
    db: Session,
    store_id: UUID,
    user_id: UUID,
    update_data: model.EtsyStoreUpdate
) -> Optional[EtsyStore]:
    """Update an Etsy store"""
    store = get_etsy_store(db, store_id, user_id)
    if not store:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(store, field, value)

    db.commit()
    db.refresh(store)
    return store

def delete_etsy_store(db: Session, store_id: UUID, user_id: UUID) -> bool:
    """Delete an Etsy store"""
    store = get_etsy_store(db, store_id, user_id)
    if not store:
        return False

    db.delete(store)
    db.commit()
    return True

# Enhanced Shopify Store operations
def get_user_shopify_stores_enhanced(db: Session, user_id: UUID) -> List[ShopifyStore]:
    """Get all Shopify stores for a user with enhanced information"""
    return db.query(ShopifyStore).filter(ShopifyStore.user_id == user_id).order_by(ShopifyStore.created_at.desc()).all()

def update_shopify_store_enhanced(
    db: Session,
    store_id: UUID,
    user_id: UUID,
    update_data: model.ShopifyStoreEnhancedUpdate
) -> Optional[ShopifyStore]:
    """Update a Shopify store with enhanced information"""
    store = db.query(ShopifyStore).filter(
        and_(
            ShopifyStore.id == store_id,
            ShopifyStore.user_id == user_id
        )
    ).first()

    if not store:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(store, field, value)

    db.commit()
    db.refresh(store)
    return store

# Bulk operations
async def verify_all_user_connections(
    db: Session,
    user_id: UUID
) -> model.BulkConnectionVerificationResponse:
    """Verify all platform connections for a user"""
    connections = get_user_platform_connections(db, user_id)
    results = []
    valid_count = 0

    for connection in connections:
        result = await verify_platform_connection(db, connection.id, user_id)
        results.append(result)
        if result.is_valid:
            valid_count += 1

    return model.BulkConnectionVerificationResponse(
        connections=results,
        total_checked=len(results),
        valid_connections=valid_count
    )

# Platform setup helper
async def setup_platform_connection(
    db: Session,
    user_id: UUID,
    setup_data: model.PlatformSetupRequest
) -> model.PlatformSetupResponse:
    """Setup a new platform connection and store in one operation"""
    try:
        # Create the platform connection
        connection = create_platform_connection(db, user_id, setup_data.connection_data)

        # Create the associated store based on platform
        store_id = None
        if setup_data.platform == model.PlatformTypeEnum.ETSY:
            etsy_store_data = model.EtsyStoreCreate(
                connection_id=connection.id,
                **setup_data.store_data
            )
            store = create_etsy_store(db, user_id, etsy_store_data)
            store_id = store.id

        elif setup_data.platform == model.PlatformTypeEnum.SHOPIFY:
            # For Shopify, update existing store with connection_id
            # This is for backward compatibility during migration
            pass

        return model.PlatformSetupResponse(
            success=True,
            message=f"Successfully set up {setup_data.platform.value} connection",
            connection=model.PlatformConnectionResponse.model_validate(connection),
            store_id=store_id
        )

    except Exception as e:
        logger.error(f"Error setting up platform connection: {e}")
        return model.PlatformSetupResponse(
            success=False,
            message=f"Failed to set up {setup_data.platform.value} connection: {str(e)}",
            connection=None,
            store_id=None
        )