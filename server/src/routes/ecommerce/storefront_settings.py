"""Storefront Settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from server.src.database.core import get_db
from server.src.entities.ecommerce.storefront_settings import StorefrontSettings
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.routes.auth.plan_access import require_pro_plan
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/admin/storefront-settings',
    tags=['Ecommerce - Storefront Settings']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class StorefrontSettingsRequest(BaseModel):
    """Storefront settings request model."""
    store_name: Optional[str] = Field(None, max_length=255)
    store_description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=512)
    primary_color: str = Field("#10b981", pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field("#059669", pattern="^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field("#34d399", pattern="^#[0-9A-Fa-f]{6}$")
    text_color: str = Field("#111827", pattern="^#[0-9A-Fa-f]{6}$")
    background_color: str = Field("#ffffff", pattern="^#[0-9A-Fa-f]{6}$")

    # Shipping Configuration
    shipping_from_name: Optional[str] = Field(None, max_length=255)
    shipping_from_company: Optional[str] = Field(None, max_length=255)
    shipping_from_street1: Optional[str] = Field(None, max_length=255)
    shipping_from_street2: Optional[str] = Field(None, max_length=255)
    shipping_from_city: Optional[str] = Field(None, max_length=100)
    shipping_from_state: Optional[str] = Field(None, max_length=50)
    shipping_from_zip: Optional[str] = Field(None, max_length=20)
    shipping_from_country: Optional[str] = Field("US", max_length=50)
    shipping_from_phone: Optional[str] = Field(None, max_length=50)
    shipping_from_email: Optional[str] = Field(None, max_length=255)

    # Default Package Dimensions
    shipping_default_length: Optional[str] = Field("10", max_length=10)
    shipping_default_width: Optional[str] = Field("8", max_length=10)
    shipping_default_height: Optional[str] = Field("4", max_length=10)
    shipping_default_weight: Optional[str] = Field("1", max_length=10)

    # Shippo API Configuration
    shippo_api_key: Optional[str] = Field(None, max_length=255)
    shippo_test_mode: Optional[str] = Field("true", max_length=10)

    # Shipping Pricing
    handling_fee: Optional[str] = Field("0.00", max_length=10)


class StorefrontSettingsResponse(BaseModel):
    """Storefront settings response model."""
    id: int
    user_id: UUID
    store_name: Optional[str] = None
    store_description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    accent_color: str
    text_color: str
    background_color: str

    # Shipping Configuration
    shipping_from_name: Optional[str] = None
    shipping_from_company: Optional[str] = None
    shipping_from_street1: Optional[str] = None
    shipping_from_street2: Optional[str] = None
    shipping_from_city: Optional[str] = None
    shipping_from_state: Optional[str] = None
    shipping_from_zip: Optional[str] = None
    shipping_from_country: Optional[str] = None
    shipping_from_phone: Optional[str] = None
    shipping_from_email: Optional[str] = None

    # Default Package Dimensions
    shipping_default_length: Optional[str] = None
    shipping_default_width: Optional[str] = None
    shipping_default_height: Optional[str] = None
    shipping_default_weight: Optional[str] = None

    # Shippo API Configuration
    shippo_api_key: Optional[str] = None
    shippo_test_mode: Optional[str] = None

    # Shipping Pricing
    handling_fee: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Routes
# ============================================================================

@router.get('/', response_model=StorefrontSettingsResponse)
async def get_storefront_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Get storefront settings for the current user.

    Returns the user's storefront branding and appearance settings.
    If settings don't exist, returns 404.

    Requires: Pro plan or higher
    """
    settings = db.query(StorefrontSettings).filter(
        StorefrontSettings.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Storefront settings not found")

    return settings


@router.post('/', response_model=StorefrontSettingsResponse)
async def upsert_storefront_settings(
    settings_data: StorefrontSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Create or update storefront settings for the current user.

    If settings already exist, they will be updated.
    If they don't exist, new settings will be created.

    Requires: Pro plan or higher
    """
    # Check if settings already exist
    settings = db.query(StorefrontSettings).filter(
        StorefrontSettings.user_id == current_user.id
    ).first()

    if settings:
        # Update existing settings
        for key, value in settings_data.dict(exclude_unset=True).items():
            setattr(settings, key, value)
    else:
        # Create new settings
        settings = StorefrontSettings(
            user_id=current_user.id,
            **settings_data.dict()
        )
        db.add(settings)

    try:
        db.commit()
        db.refresh(settings)
        return settings
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")


@router.delete('/')
async def delete_storefront_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Delete storefront settings for the current user.

    Resets settings to defaults by deleting the record.

    Requires: Pro plan or higher
    """
    settings = db.query(StorefrontSettings).filter(
        StorefrontSettings.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Storefront settings not found")

    try:
        db.delete(settings)
        db.commit()
        return {"message": "Storefront settings deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete settings: {str(e)}")


@router.get('/public/{user_id}', response_model=StorefrontSettingsResponse)
async def get_public_storefront_settings(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get public storefront settings for a specific user.

    This endpoint is public and doesn't require authentication.
    Used by the storefront to fetch branding settings.

    If user_id is "1" or invalid UUID, returns the first user's settings or defaults.
    """
    # Try to convert string UUID to UUID object
    try:
        user_uuid = UUID(user_id)
        settings = db.query(StorefrontSettings).filter(
            StorefrontSettings.user_id == user_uuid
        ).first()
    except ValueError:
        # If not a valid UUID (e.g., "1"), try to get the first available settings
        settings = db.query(StorefrontSettings).first()

    if not settings:
        # Return default settings if none exist
        # Use a dummy UUID for the response
        from uuid import uuid4
        return StorefrontSettingsResponse(
            id=0,
            user_id=uuid4(),
            store_name=None,
            store_description=None,
            logo_url=None,
            primary_color="#10b981",
            secondary_color="#059669",
            accent_color="#34d399",
            text_color="#111827",
            background_color="#ffffff"
        )

    return settings
