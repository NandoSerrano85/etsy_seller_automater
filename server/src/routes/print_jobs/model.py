"""
Print Job models for API requests and responses
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class PrintJobType(str, Enum):
    GANG_SHEETS = "gang_sheets"
    MOCKUPS = "mockups"
    DESIGNS = "designs"
    ORDERS = "orders"
    PRINT_FILES = "print_files"

class PrintJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Request Models
class PrintJobCreate(BaseModel):
    job_type: PrintJobType
    template_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    input_data: Dict[str, Any] = Field(default_factory=dict)

class PrintJobUpdate(BaseModel):
    status: Optional[PrintJobStatus] = None
    config: Optional[Dict[str, Any]] = None
    input_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class PrintJobSearch(BaseModel):
    job_type: Optional[PrintJobType] = None
    status: Optional[PrintJobStatus] = None
    template_name: Optional[str] = None
    created_by: Optional[UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# Response Models
class PrintJobResponse(BaseModel):
    id: UUID
    org_id: UUID
    created_by: Optional[UUID] = None
    job_type: PrintJobType
    status: PrintJobStatus
    template_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_files: List[UUID] = Field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PrintJobListResponse(BaseModel):
    jobs: List[PrintJobResponse]
    total: int
    limit: int
    offset: int

class PrintJobStatsResponse(BaseModel):
    total_jobs: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    avg_processing_time: Optional[float] = None  # in seconds
    
class JobQueueResponse(BaseModel):
    queued_jobs: int
    processing_jobs: int
    estimated_wait_time: Optional[int] = None  # in seconds