"""
Event/Audit API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional

from server.src.database import get_db
from server.src.auth.dependencies import get_current_user
from server.src.entities.user import User
from server.src.routes.organizations.service import OrganizationService
from . import model
from .service import EventService

router = APIRouter(prefix="/organizations/{org_id}/events", tags=["events"])

@router.post("/", response_model=model.EventResponse)
def create_event(
    org_id: UUID,
    event_data: model.EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new event (for external integrations)"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    try:
        event = EventService.create_event(
            db=db,
            org_id=org_id,
            user_id=current_user.id,
            event_data=event_data
        )
        return model.EventResponse.model_validate(event)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=model.EventListResponse)
def search_events(
    org_id: UUID,
    event_type: Optional[model.EventTypeFilter] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    payload_contains: Optional[str] = None,
    hours_back: Optional[int] = Query(None, ge=1, le=8760, description="Events from last N hours"),
    days_back: Optional[int] = Query(None, ge=1, le=365, description="Events from last N days"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search events with filters"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    # Set time filters based on convenience parameters
    created_after = None
    if hours_back:
        created_after = datetime.utcnow() - timedelta(hours=hours_back)
    elif days_back:
        created_after = datetime.utcnow() - timedelta(days=days_back)
    
    search_params = model.EventSearchRequest(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        payload_contains=payload_contains,
        created_after=created_after
    )
    
    events, total = EventService.search_events(
        db=db,
        org_id=org_id,
        search_params=search_params,
        skip=skip,
        limit=limit
    )
    
    return model.EventListResponse(
        events=[model.EventResponse.model_validate(event) for event in events],
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/{event_id}", response_model=model.EventResponse)
def get_event(
    org_id: UUID,
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event by ID"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    event = EventService.get_event_by_id(db=db, event_id=event_id)
    if not event or event.org_id != org_id:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return model.EventResponse.model_validate(event)

@router.get("/audit/{entity_type}/{entity_id}", response_model=model.AuditTrailResponse)
def get_audit_trail(
    org_id: UUID,
    entity_type: str,
    entity_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for specific entity"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    events = EventService.get_audit_trail(
        db=db,
        org_id=org_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit
    )
    
    return model.AuditTrailResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        events=[model.EventResponse.model_validate(event) for event in events],
        total_events=len(events)
    )

@router.get("/activity/user/{user_id}", response_model=model.EventListResponse)
def get_user_activity(
    org_id: UUID,
    user_id: UUID,
    hours: int = Query(24, ge=1, le=168, description="Hours of activity to retrieve"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent user activity"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    events = EventService.get_user_activity(
        db=db,
        org_id=org_id,
        user_id=user_id,
        hours=hours,
        limit=limit
    )
    
    return model.EventListResponse(
        events=[model.EventResponse.model_validate(event) for event in events],
        total=len(events),
        limit=limit,
        offset=0
    )

@router.get("/activity/errors", response_model=model.EventListResponse)
def get_system_errors(
    org_id: UUID,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for errors"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent system errors"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    events = EventService.get_system_errors(
        db=db,
        org_id=org_id,
        hours=hours,
        limit=limit
    )
    
    return model.EventListResponse(
        events=[model.EventResponse.model_validate(event) for event in events],
        total=len(events),
        limit=limit,
        offset=0
    )

@router.get("/stats/summary", response_model=model.EventStatsResponse)
def get_event_stats(
    org_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event statistics for organization"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    stats = EventService.get_event_stats(db=db, org_id=org_id, days=days)
    
    return model.EventStatsResponse(
        total_events=stats.get("total_events", 0),
        by_type=stats.get("by_type", {}),
        by_entity_type=stats.get("by_entity_type", {}),
        recent_activity_count=stats.get("recent_activity_count", 0)
    )

@router.get("/export/audit-trail")
def export_audit_trail(
    org_id: UUID,
    start_date: datetime = Query(..., description="Start date for export"),
    end_date: datetime = Query(..., description="End date for export"),
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export audit trail for compliance purposes"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    # Validate date range
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    events = EventService.export_audit_trail(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    # Return as JSON for now - in production you might want CSV/Excel export
    return {
        "export_info": {
            "org_id": org_id,
            "start_date": start_date,
            "end_date": end_date,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_events": len(events)
        },
        "events": [model.EventResponse.model_validate(event) for event in events]
    }

# System-wide routes (admin only)
@router.get("/system/activity", response_model=model.EventListResponse)
def get_recent_system_activity(
    hours: int = Query(1, ge=1, le=24, description="Hours of system activity"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent system activity across all organizations (admin only)"""
    # TODO: Add admin role check
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    events = EventService.get_recent_system_activity(db=db, hours=hours, limit=limit)
    
    return model.EventListResponse(
        events=[model.EventResponse.model_validate(event) for event in events],
        total=len(events),
        limit=limit,
        offset=0
    )