from typing import Optional, Union, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class EtsyProductTemplateCreate(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    who_made: Optional[str] = None
    when_made: Optional[str] = None
    taxonomy_id: Optional[int] = None
    price: Optional[float] = None
    materials: Optional[Union[str, List[str]]] = None
    shop_section_id: Optional[int] = None
    quantity: Optional[int] = None
    tags: Optional[Union[str, List[str]]] = None
    item_weight: Optional[float] = None
    item_weight_unit: Optional[str] = None
    item_length: Optional[float] = None
    item_width: Optional[float] = None
    item_height: Optional[float] = None
    item_dimensions_unit: Optional[str] = None
    is_taxable: Optional[bool] = None
    type: Optional[str] = None
    processing_min: Optional[int] = None
    processing_max: Optional[int] = None
    return_policy_id: Optional[int] = None
    production_partner_ids: Optional[str] = None  # Comma-separated list of production partner IDs

class EtsyProductTemplateUpdate(EtsyProductTemplateCreate):
    pass

class EtsyProductTemplateResponse(EtsyProductTemplateCreate):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class EtsyProductTemplateData(BaseModel):
    product_template_id: str | None = None
    def get_uuid(self) -> UUID | None:
        if self.product_template_id:
            return UUID(self.product_template_id)
        return None
