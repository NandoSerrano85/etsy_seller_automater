from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class SizeConfigCreate(BaseModel):
    name: str
    width_inches: float
    height_inches: float
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SizeConfigUpdate(SizeConfigCreate):
    pass

class SizeConfigResponse(SizeConfigCreate):
    id: UUID
    product_template_id: UUID
    canvas_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SizeConfigWithRelationsResponse(SizeConfigResponse):
    """Response model that includes related data"""
    product_template_name: Optional[str] = None
    canvas_config_name: Optional[str] = None
    design_images_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class SizeConfigListResponse(BaseModel):
    """Response model for listing size configs with pagination info"""
    items: List[SizeConfigResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)