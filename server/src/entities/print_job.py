"""
Print Job Entity for Background Processing
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from ..database.core import Base

class PrintJobStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PrintJobType(enum.Enum):
    GANG_SHEETS = "gang_sheets"
    MOCKUPS = "mockups"
    DESIGNS = "designs"
    ORDERS = "orders"
    PRINT_FILES = "print_files"

class PrintJob(Base):
    __tablename__ = 'print_jobs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    
    # Job configuration
    job_type = Column(Enum(PrintJobType), nullable=False)
    status = Column(Enum(PrintJobStatus), default=PrintJobStatus.QUEUED)
    template_name = Column(String(255))
    
    # Job data
    config = Column(JSONB, default={})  # Job-specific configuration
    input_data = Column(JSONB, default={})  # Input parameters (order IDs, design IDs, etc.)
    output_files = Column(ARRAY(UUID), default=[])  # Array of file IDs that were generated
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(String(10), default='0')
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", back_populates="print_jobs")
    created_by_user = relationship("User", back_populates="print_jobs")
    
    def __repr__(self):
        return f"<PrintJob(id={self.id}, type={self.job_type}, status={self.status})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'org_id': str(self.org_id),
            'created_by': str(self.created_by) if self.created_by else None,
            'job_type': self.job_type.value if self.job_type else None,
            'status': self.status.value if self.status else None,
            'template_name': self.template_name,
            'config': self.config,
            'input_data': self.input_data,
            'output_files': [str(file_id) for file_id in (self.output_files or [])],
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def mark_started(self):
        """Mark job as started"""
        self.status = PrintJobStatus.PROCESSING
        self.started_at = datetime.now(timezone.utc)
    
    def mark_completed(self, output_files: list = None):
        """Mark job as completed"""
        self.status = PrintJobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if output_files:
            self.output_files = output_files
    
    def mark_failed(self, error_message: str):
        """Mark job as failed"""
        self.status = PrintJobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message
    
    @property
    def duration_seconds(self) -> float:
        """Calculate job duration in seconds"""
        if not self.started_at:
            return 0
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()