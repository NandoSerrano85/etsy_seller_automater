"""
Shop service layer for business logic
"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.src.entities.shop import Shop
from server.src.entities.event import Event, EventTypes
from . import model

logger = logging.getLogger(__name__)

class ShopService:
    
    @staticmethod
    def create_shop(
        db: Session,
        org_id: UUID,
        shop_data: model.ShopCreate,
        user_id: Optional[UUID] = None
    ) -> Shop:
        """Create a new shop connection"""
        try:
            # Check if shop already exists for this org and provider
            existing_shop = db.query(Shop).filter(
                Shop.org_id == org_id,
                Shop.provider == shop_data.provider,
                Shop.provider_shop_id == shop_data.provider_shop_id
            ).first()
            
            if existing_shop:
                raise ValueError(f"Shop {shop_data.provider_shop_id} already exists for this organization")
            
            shop = Shop(
                org_id=org_id,
                provider=shop_data.provider,
                provider_shop_id=shop_data.provider_shop_id,
                display_name=shop_data.display_name,
                access_token=shop_data.access_token,
                refresh_token=shop_data.refresh_token
            )
            db.add(shop)
            db.flush()
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=org_id,
                user_id=user_id,
                entity_type="Shop",
                entity_id=shop.id,
                payload={
                    "action": "shop_connected",
                    "provider": shop_data.provider,
                    "provider_shop_id": shop_data.provider_shop_id
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(shop)
            
            logger.info(f"Created shop connection: {shop.id} - {shop.provider}:{shop.provider_shop_id}")
            return shop
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating shop: {e}")
            raise

    @staticmethod
    def get_shop_by_id(db: Session, shop_id: UUID) -> Optional[Shop]:
        """Get shop by ID"""
        return db.query(Shop).filter(Shop.id == shop_id).first()

    @staticmethod
    def get_shops_by_org(
        db: Session,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Shop], int]:
        """Get paginated list of shops for organization"""
        query = db.query(Shop).filter(Shop.org_id == org_id)
        total = query.count()
        shops = query.offset(skip).limit(limit).all()
        return shops, total

    @staticmethod
    def get_shop_by_provider(
        db: Session,
        org_id: UUID,
        provider: str,
        provider_shop_id: str
    ) -> Optional[Shop]:
        """Get shop by provider and provider shop ID"""
        return db.query(Shop).filter(
            Shop.org_id == org_id,
            Shop.provider == provider,
            Shop.provider_shop_id == provider_shop_id
        ).first()

    @staticmethod
    def update_shop(
        db: Session,
        shop_id: UUID,
        shop_data: model.ShopUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[Shop]:
        """Update shop connection"""
        try:
            shop = db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                return None
            
            # Update fields
            update_data = shop_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(shop, field, value)
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=shop.org_id,
                user_id=user_id,
                entity_type="Shop",
                entity_id=shop_id,
                payload={"action": "shop_updated", "changes": update_data}
            )
            db.add(event)
            
            db.commit()
            db.refresh(shop)
            
            logger.info(f"Updated shop: {shop_id}")
            return shop
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating shop {shop_id}: {e}")
            raise

    @staticmethod
    def delete_shop(db: Session, shop_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete shop connection"""
        try:
            shop = db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                return False
            
            # Log event before deletion
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_WARNING,
                org_id=shop.org_id,
                user_id=user_id,
                entity_type="Shop",
                entity_id=shop_id,
                payload={
                    "action": "shop_disconnected",
                    "provider": shop.provider,
                    "provider_shop_id": shop.provider_shop_id
                }
            )
            db.add(event)
            db.flush()
            
            # Delete shop
            db.delete(shop)
            db.commit()
            
            logger.warning(f"Deleted shop: {shop_id} - {shop.provider}:{shop.provider_shop_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting shop {shop_id}: {e}")
            raise

    @staticmethod
    def update_last_sync(db: Session, shop_id: UUID) -> bool:
        """Update last sync timestamp for shop"""
        try:
            shop = db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                return False
            
            from datetime import datetime
            shop.last_sync_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating last sync for shop {shop_id}: {e}")
            return False