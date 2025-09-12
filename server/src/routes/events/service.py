"""
Event/Audit service layer for system monitoring and audit trails
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from server.src.entities.event import Event, EventTypes
from . import model

logger = logging.getLogger(__name__)

class EventService:
    
    @staticmethod
    def create_event(
        db: Session,
        org_id: Optional[UUID],
        user_id: Optional[UUID],
        event_data: model.EventCreate
    ) -> Event:
        """Create a new event"""
        try:
            event = Event.create_event(
                event_type=event_data.event_type,
                org_id=org_id,
                user_id=user_id,
                entity_type=event_data.entity_type,
                entity_id=event_data.entity_id,
                payload=event_data.payload
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            
            logger.debug(f"Created event: {event.id} - {event.event_type}")
            return event
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating event: {e}")
            raise

    @staticmethod
    def get_event_by_id(db: Session, event_id: UUID) -> Optional[Event]:
        """Get event by ID"""
        return db.query(Event).filter(Event.id == event_id).first()

    @staticmethod
    def search_events(
        db: Session,
        org_id: UUID,
        search_params: model.EventSearchRequest,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Event], int]:
        """Search events with filters"""
        query = db.query(Event).filter(Event.org_id == org_id)
        
        # Apply filters
        if search_params.event_type:
            query = query.filter(Event.event_type == search_params.event_type.value)
        
        if search_params.entity_type:
            query = query.filter(Event.entity_type == search_params.entity_type)
        
        if search_params.entity_id:
            query = query.filter(Event.entity_id == search_params.entity_id)
        
        if search_params.user_id:
            query = query.filter(Event.user_id == search_params.user_id)
        
        if search_params.payload_contains:
            # Search in JSON payload
            query = query.filter(
                Event.payload.op('->>')('action').ilike(f"%{search_params.payload_contains}%")
            )
        
        if search_params.created_after:
            query = query.filter(Event.created_at >= search_params.created_after)
        
        if search_params.created_before:
            query = query.filter(Event.created_at <= search_params.created_before)
        
        # Order by creation date descending
        query = query.order_by(desc(Event.created_at))
        
        total = query.count()
        events = query.offset(skip).limit(limit).all()
        return events, total

    @staticmethod
    def get_audit_trail(
        db: Session,
        org_id: UUID,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[Event]:
        """Get audit trail for specific entity"""
        return db.query(Event).filter(
            Event.org_id == org_id,
            Event.entity_type == entity_type,
            Event.entity_id == entity_id
        ).order_by(desc(Event.created_at)).limit(limit).all()

    @staticmethod
    def get_user_activity(
        db: Session,
        org_id: UUID,
        user_id: UUID,
        hours: int = 24,
        limit: int = 100
    ) -> List[Event]:
        """Get recent user activity"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        return db.query(Event).filter(
            Event.org_id == org_id,
            Event.user_id == user_id,
            Event.created_at >= since
        ).order_by(desc(Event.created_at)).limit(limit).all()

    @staticmethod
    def get_system_errors(
        db: Session,
        org_id: Optional[UUID] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Event]:
        """Get recent system errors"""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(Event).filter(
            Event.event_type == EventTypes.SYSTEM_ERROR,
            Event.created_at >= since
        )
        
        if org_id:
            query = query.filter(Event.org_id == org_id)
        
        return query.order_by(desc(Event.created_at)).limit(limit).all()

    @staticmethod
    def get_event_stats(db: Session, org_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get event statistics for organization"""
        try:
            # Date range for stats
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total events
            total_events = db.query(func.count(Event.id)).filter(
                Event.org_id == org_id,
                Event.created_at >= start_date
            ).scalar() or 0
            
            # Events by type
            type_stats = db.query(
                Event.event_type,
                func.count(Event.id).label('count')
            ).filter(
                Event.org_id == org_id,
                Event.created_at >= start_date
            ).group_by(Event.event_type).all()
            
            # Events by entity type
            entity_stats = db.query(
                Event.entity_type,
                func.count(Event.id).label('count')
            ).filter(
                Event.org_id == org_id,
                Event.created_at >= start_date,
                Event.entity_type.isnot(None)
            ).group_by(Event.entity_type).all()
            
            # Recent activity (last 24 hours)
            recent_activity = db.query(func.count(Event.id)).filter(
                Event.org_id == org_id,
                Event.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).scalar() or 0
            
            return {
                "total_events": total_events,
                "by_type": {event_type: count for event_type, count in type_stats},
                "by_entity_type": {entity_type: count for entity_type, count in entity_stats if entity_type},
                "recent_activity_count": recent_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting event stats for org {org_id}: {e}")
            return {}

    @staticmethod
    def cleanup_old_events(db: Session, days_to_keep: int = 90) -> int:
        """Clean up old events (run as maintenance task)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old events except for important ones
            deleted_count = db.query(Event).filter(
                Event.created_at < cutoff_date,
                Event.event_type.notin_([EventTypes.SYSTEM_ERROR, EventTypes.SYSTEM_WARNING])
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old events")
            return deleted_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up old events: {e}")
            return 0

    @staticmethod
    def get_recent_system_activity(db: Session, hours: int = 1, limit: int = 50) -> List[Event]:
        """Get recent system activity across all organizations"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        return db.query(Event).filter(
            Event.created_at >= since,
            Event.event_type.in_([EventTypes.SYSTEM_INFO, EventTypes.SYSTEM_WARNING, EventTypes.SYSTEM_ERROR])
        ).order_by(desc(Event.created_at)).limit(limit).all()

    @staticmethod
    def export_audit_trail(
        db: Session,
        org_id: UUID,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None
    ) -> List[Event]:
        """Export audit trail for compliance purposes"""
        query = db.query(Event).filter(
            Event.org_id == org_id,
            Event.created_at >= start_date,
            Event.created_at <= end_date
        )
        
        if entity_type:
            query = query.filter(Event.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(Event.entity_id == entity_id)
        
        return query.order_by(Event.created_at.asc()).all()