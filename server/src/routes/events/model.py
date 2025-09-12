"""
Event/Audit models for API requests and responses
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class EventTypeFilter(str, Enum):
    SYSTEM_INFO = "SYSTEM_INFO"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    USER_ACTION = "USER_ACTION"
    API_CALL = "API_CALL"

# Request Models
class EventSearchRequest(BaseModel):
    event_type: Optional[EventTypeFilter] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    payload_contains: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class EventCreate(BaseModel):
    event_type: str = Field(..., description="Event type identifier")
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

# Response Models
class EventResponse(BaseModel):
    id: UUID
    org_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True

class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    limit: int
    offset: int

class EventStatsResponse(BaseModel):
    total_events: int
    by_type: Dict[str, int]
    by_entity_type: Dict[str, int]
    recent_activity_count: int  # Events in last 24 hours

class AuditTrailResponse(BaseModel):
    entity_type: str
    entity_id: UUID
    events: List[EventResponse]
    total_events: int