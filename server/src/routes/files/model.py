"""
File models for API requests and responses
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class FileTypeEnum(str, Enum):
    ORIGINAL = "original"
    DESIGN = "design"
    MOCKUP = "mockup"
    PRINT_FILE = "print_file"
    WATERMARK = "watermark"
    TEMPLATE = "template"
    EXPORT = "export"
    OTHER = "other"

class FileStatusEnum(str, Enum):
    UPLOADING = "uploading"
    READY = "ready"
    PROCESSING = "processing"
    FAILED = "failed"
    ARCHIVED = "archived"

# Request Models
class FileUploadRequest(BaseModel):
    file_type: FileTypeEnum
    filename: str = Field(..., description="Original filename")
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FileUpdateRequest(BaseModel):
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[FileStatusEnum] = None

class FileSearchRequest(BaseModel):
    file_type: Optional[FileTypeEnum] = None
    status: Optional[FileStatusEnum] = None
    filename_contains: Optional[str] = None
    sha256: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# Response Models
class FileResponse(BaseModel):
    id: UUID
    org_id: UUID
    file_type: FileTypeEnum
    status: FileStatusEnum
    nas_path: str
    filename: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sha256: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int
    limit: int
    offset: int

class FileUploadResponse(BaseModel):
    file_id: UUID
    upload_url: Optional[str] = None  # For direct upload scenarios
    nas_path: str
    message: str