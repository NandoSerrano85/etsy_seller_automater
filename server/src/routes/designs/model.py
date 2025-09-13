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
    is_digital: bool = False

class DesignImageCreate(BaseModel):
    product_template_id: UUID
    starting_name: int = 100
    mockup_id: UUID
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    is_active: bool = True
    is_digital: bool = False
    filename: str = ''
    file_path: str = ''

class DesignImageUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_digital: Optional[bool] = None

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

class EtsyMockupImage(BaseModel):
    filename: str
    url: str
    path: Optional[str] = None  # For compatibility with frontend
    etsy_listing_id: Optional[str] = None
    image_id: Optional[str] = None

class DesignFile(BaseModel):
    filename: str
    path: str
    url: Optional[str] = None  # For compatibility with frontend
    template_name: str
    nas_path: str
    file_size: Optional[int] = None
    last_modified: Optional[datetime] = None

class DesignGalleryResponse(BaseModel):
    mockups: List[EtsyMockupImage]
    files: List[DesignFile]
    total_mockups: int
    total_files: int
