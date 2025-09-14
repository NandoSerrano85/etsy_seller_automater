from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

# Template Editor specific models

class DesignArea(BaseModel):
    """Design area coordinates and properties"""
    x: float
    y: float
    width: float
    height: float
    rotation: Optional[float] = 0
    name: Optional[str] = "Design Area"

class TemplateEditorCreate(BaseModel):
    """Create a new template with mockup background and design areas"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    background_image_data: str  # Base64 encoded image data
    background_filename: str
    design_areas: List[DesignArea]
    metadata: Optional[Dict[str, Any]] = {}

class TemplateEditorUpdate(BaseModel):
    """Update existing template"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    background_image_data: Optional[str] = None
    background_filename: Optional[str] = None
    design_areas: Optional[List[DesignArea]] = None
    metadata: Optional[Dict[str, Any]] = None

class TemplateEditorResponse(BaseModel):
    """Template editor response"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    background_image_url: str
    background_filename: str
    design_areas: List[DesignArea]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TemplatePreview(BaseModel):
    """Preview template with overlay"""
    template_id: UUID
    design_image_data: Optional[str] = None  # Base64 encoded design image
    design_filename: Optional[str] = None

class TemplatePreviewResponse(BaseModel):
    """Preview response with rendered mockup"""
    preview_image_url: str
    template_data: TemplateEditorResponse

class TemplateListResponse(BaseModel):
    """List of templates"""
    templates: List[TemplateEditorResponse]
    total: int
    page: int
    per_page: int