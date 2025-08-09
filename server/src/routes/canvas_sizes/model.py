from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class CanvasConfigCreate(BaseModel):
    name: str
    width_inches: float
    height_inches: float
    description: Optional[str] = None
    is_active: bool
    is_stretch: bool

class CanvasConfigUpdate(CanvasConfigCreate):
    pass

class CanvasConfigResponse(CanvasConfigCreate):
    id: UUID
    product_template_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CanvasConfigData(BaseModel):
    canvas_config_id: str | None = None
    def get_uuid(self) -> UUID | None:
        if self.canvas_config_id:
            return UUID(self.canvas_config_id)
        return None
