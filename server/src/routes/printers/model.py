"""
Printer models for API requests and responses
"""

from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum

class PrinterTypeEnum(str, Enum):
    UVDTF = "uvdtf"  # UV Direct to Film
    DTF = "dtf"      # Direct to Film
    SUBLIMATION = "sublimation"
    VINYL = "vinyl"  # Vinyl cutting/printing

# Request Models
class PrinterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Printer name")
    printer_type: PrinterTypeEnum = Field(default=PrinterTypeEnum.DTF)
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    max_width_inches: float = Field(..., gt=0, le=500, description="Maximum print width in inches")
    max_height_inches: float = Field(..., gt=0, le=500, description="Maximum print height in inches")
    dpi: int = Field(default=300, ge=150, le=1200, description="Printer DPI")
    supported_template_ids: List[UUID] = Field(default_factory=list)
    is_default: bool = Field(default=False, description="Set as default printer")
    
    @validator('dpi')
    def validate_dpi(cls, v):
        suggested_dpis = [150, 200, 300, 400, 500, 600, 720, 1200]
        if v not in suggested_dpis:
            # Allow custom DPI but warn about common values
            pass
        return v

class PrinterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    printer_type: Optional[PrinterTypeEnum] = None
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    max_width_inches: Optional[float] = Field(None, gt=0, le=500)
    max_height_inches: Optional[float] = Field(None, gt=0, le=500)
    dpi: Optional[int] = Field(None, ge=150, le=1200)
    supported_template_ids: Optional[List[UUID]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class PrinterCapabilityCheck(BaseModel):
    width_inches: float = Field(..., gt=0)
    height_inches: float = Field(..., gt=0)
    template_id: Optional[UUID] = None

# Response Models
class PrinterResponse(BaseModel):
    id: UUID
    user_id: UUID
    org_id: Optional[UUID] = None  # Made optional for backward compatibility
    name: str
    printer_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    description: Optional[str] = None
    max_width_inches: float
    max_height_inches: float
    dpi: int
    supported_template_ids: List[UUID] = Field(default_factory=list)
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    # Computed properties
    print_area_description: str = ""
    is_large_format: bool = False

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        # Compute derived properties
        self.print_area_description = f"{self.max_width_inches}\" x {self.max_height_inches}\""
        self.is_large_format = self.max_width_inches > 13 or self.max_height_inches > 13

class PrinterListResponse(BaseModel):
    printers: List[PrinterResponse]
    total: int
    limit: int
    offset: int

class PrinterCapabilityResponse(BaseModel):
    can_print: bool
    printer_id: UUID
    printer_name: str
    width_fits: bool
    height_fits: bool
    template_supported: Optional[bool] = None
    reason: Optional[str] = None

class PrinterSuggestionsResponse(BaseModel):
    dpi_suggestions: List[int]
    printer_types: List[str]
    common_sizes: List[dict]  # Common printer sizes with descriptions

class PrinterStatsResponse(BaseModel):
    total_printers: int
    active_printers: int
    by_type: dict
    default_printer_id: Optional[UUID] = None
    average_dpi: Optional[float] = None