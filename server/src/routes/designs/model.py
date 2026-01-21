from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

class DesignImageBase(BaseModel):
    filename: str
    file_path: str
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    platform: str = 'etsy'  # 'etsy' or 'shopify'
    is_active: bool = True
    is_digital: Optional[bool] = False  # Allow None for backwards compatibility
    tags: Optional[List[str]] = []  # AI-generated tags
    tags_metadata: Optional[Dict[str, Any]] = None  # Tag generation metadata

class DesignImageCreate(BaseModel):
    product_template_id: UUID
    starting_name: int = 100
    mockup_id: UUID
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    platform: str = 'etsy'  # 'etsy' or 'shopify' - will be auto-detected from template
    is_active: bool = True
    is_digital: bool = False
    filename: str = ''
    file_path: str = ''
    file_formats: Optional[List[str]] = ['png']  # Supported formats: png, svg, psd

class DesignImageUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None
    canvas_config_id: Optional[UUID] = None
    size_config_id: Optional[UUID] = None
    platform: Optional[str] = None  # 'etsy' or 'shopify'
    is_active: Optional[bool] = None
    is_digital: Optional[bool] = None
    tags: Optional[List[str]] = None  # AI-generated tags
    tags_metadata: Optional[Dict[str, Any]] = None  # Tag generation metadata

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
