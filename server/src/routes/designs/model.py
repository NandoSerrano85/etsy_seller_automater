from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class DesignImageBase(BaseModel):
    filename: str
    file_path: str
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    is_active: bool = True

class DesignImageCreate(DesignImageBase):
    pass

class DesignImageUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class DesignImageResponse(DesignImageBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DesignImageListResponse(BaseModel):
    designs: List[DesignImageResponse]
    total: int
