"""
Event Entity for Audit Logging and System Events
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from ..database.core import Base

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    
    # Event information
    event_type = Column(String(100), nullable=False)  # 'user_login', 'file_upload', 'mockup_created', etc.
    entity_type = Column(String(100))  # 'User', 'File', 'Mockup', etc.
    entity_id = Column(UUID(as_uuid=True))  # ID of the entity that was affected
    
    # Event payload
    payload = Column(JSONB, default={})  # Additional event data
    
    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_events_org_type', 'org_id', 'event_type'),
        Index('idx_events_user_created', 'user_id', 'created_at'),
        Index('idx_events_entity', 'entity_type', 'entity_id'),
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="events")
    user = relationship("User", back_populates="events")
    
    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, entity={self.entity_type})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'org_id': str(self.org_id) if self.org_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'event_type': self.event_type,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'payload': self.payload,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_event(
        cls,
        event_type: str,
        org_id: str = None,
        user_id: str = None,
        entity_type: str = None,
        entity_id: str = None,
        payload: dict = None
    ):
        """Helper method to create event records"""
        return cls(
            event_type=event_type,
            org_id=org_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {}
        )

# Common event types as constants
class EventTypes:
    # User events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_UPDATE = "user_update"
    
    # File events
    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"
    FILE_PROCESS = "file_process"
    
    # Mockup events
    MOCKUP_CREATE = "mockup_create"
    MOCKUP_UPDATE = "mockup_update"
    MOCKUP_DELETE = "mockup_delete"
    MOCKUP_GENERATE = "mockup_generate"
    
    # Design events
    DESIGN_UPLOAD = "design_upload"
    DESIGN_PROCESS = "design_process"
    DESIGN_DELETE = "design_delete"
    
    # Print events
    PRINT_JOB_CREATE = "print_job_create"
    PRINT_JOB_START = "print_job_start"
    PRINT_JOB_COMPLETE = "print_job_complete"
    PRINT_JOB_FAIL = "print_job_fail"
    
    # Shop events
    SHOP_CONNECT = "shop_connect"
    SHOP_SYNC = "shop_sync"
    SHOP_DISCONNECT = "shop_disconnect"
    
    # Order events
    ORDER_RECEIVED = "order_received"
    ORDER_PROCESS = "order_process"
    ORDER_COMPLETE = "order_complete"
    
    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"