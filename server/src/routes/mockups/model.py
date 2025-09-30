from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

# --- MockupMaskData Models ---
# Entity fields: id, mockup_image_id, masks (JSON), points (JSON), is_cropped, alignment, created_at, updated_at

class MockupMaskDataBase(BaseModel):
    masks: List[List[List[float]]]  # List of masks, each mask is a list of [x, y] points
    points: List[List[List[float]]]  # List of points, each is a list of [x, y] points
    is_cropped: bool = False  # Deprecated: Use is_cropped_list for individual mask properties
    alignment: str  # Deprecated: Use alignment_list for individual mask properties
    # New fields for individual mask properties
    is_cropped_list: Optional[List[bool]] = None  # Per-mask cropping settings
    alignment_list: Optional[List[str]] = None  # Per-mask alignment settings

class MockupMaskDataCreate(MockupMaskDataBase):
    mockup_image_id: UUID

class MockupMaskDataUpdate(BaseModel):
    masks: Optional[List[List[List[float]]]] = None
    points: Optional[List[List[List[float]]]] = None
    is_cropped: Optional[bool] = None  # Deprecated: Use is_cropped_list for individual mask properties
    alignment: Optional[str] = None  # Deprecated: Use alignment_list for individual mask properties
    # New fields for individual mask properties
    is_cropped_list: Optional[List[bool]] = None  # Per-mask cropping settings
    alignment_list: Optional[List[str]] = None  # Per-mask alignment settings

class MockupMaskDataResponse(MockupMaskDataBase):
    id: UUID
    mockup_image_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Include the new individual mask properties
    is_cropped_list: Optional[List[bool]] = None
    alignment_list: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)

# --- MockupImage Models ---
# Entity fields: id, mockups_id, filename, file_path, watermark_path, image_type, created_at, updated_at

class MockupImageBase(BaseModel):
    filename: str
    file_path: str
    watermark_path: Optional[str] = None
    image_type: Optional[str] = None

class MockupImageCreate(MockupImageBase):
    mockups_id: UUID
    design_file_path: str  # Path to the design file to use for creating mockups

class MockupImageUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    watermark_path: Optional[str] = None
    image_type: Optional[str] = None

class MockupImageResponse(MockupImageBase):
    id: UUID
    mockups_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    mask_data: Optional[List[MockupMaskDataResponse]] = None
    model_config = ConfigDict(from_attributes=True)

class MockupImageWatermarkUpdate(BaseModel):
    watermark_path: str

# --- Mockups Models ---
# Entity fields: id, user_id, product_template_id, starting_name, created_at, updated_at

class MockupsBase(BaseModel):
    starting_name: int = 100

class MockupsCreate(MockupsBase):
    product_template_id: UUID
    name: str
    # user_id is inferred from auth/session, not passed by client

class MockupsUpdate(BaseModel):
    starting_name: Optional[int] = None
    name: Optional[str] = None

class MockupsResponse(MockupsBase):
    id: UUID
    user_id: UUID
    product_template_id: UUID
    name: str
    created_at: datetime
    product_template_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    mockup_images: Optional[List[MockupImageResponse]] = None
    model_config = ConfigDict(from_attributes=True)

class MockupFullCreate(BaseModel):
    id: UUID
    product_template_id: UUID
    design_file_path: List[str]
    watermark_path: Optional[str] = None
    # Optionally, add more fields if needed for full creation

# --- List Response Models ---

class MockupsListResponse(BaseModel):
    mockups: List[MockupsResponse]
    total: int

class MockupMaskDataListResponse(BaseModel):
    mask_data: List[MockupMaskDataResponse]
    total: int

class MockupImageListResponse(BaseModel):
    mockup_images: List[MockupImageResponse]
    total: int

class MockupImageUploadResponse(BaseModel):
    uploaded_images: List[MockupImageResponse]
    total: int

# --- Upload To Etsy Models ---
class UploadToEtsyRequest(BaseModel):
    design_ids: List[UUID]  # List of design IDs to upload
    mockup_id: UUID  # ID of the mockup to upload
    product_template_id: UUID  # ID of the product template

class UploadToEtsyResponse(BaseModel):
    success: bool
    success_code: int
    message: str