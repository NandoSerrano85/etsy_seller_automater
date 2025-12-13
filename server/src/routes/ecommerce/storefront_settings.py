"""Storefront Settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from server.src.database.core import get_db
from server.src.entities.ecommerce.storefront_settings import StorefrontSettings
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/storefront-settings',
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


class StorefrontSettingsResponse(BaseModel):
    """Storefront settings response model."""
    id: int
    user_id: int
    store_name: Optional[str] = None
    store_description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    accent_color: str
    text_color: str
    background_color: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Routes
# ============================================================================

@router.get('/', response_model=StorefrontSettingsResponse)
async def get_storefront_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get storefront settings for the current user.

    Returns the user's storefront branding and appearance settings.
    If settings don't exist, returns 404.
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
    current_user: User = Depends(get_current_user)
):
    """
    Create or update storefront settings for the current user.

    If settings already exist, they will be updated.
    If they don't exist, new settings will be created.
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
    current_user: User = Depends(get_current_user)
):
    """
    Delete storefront settings for the current user.

    Resets settings to defaults by deleting the record.
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
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get public storefront settings for a specific user.

    This endpoint is public and doesn't require authentication.
    Used by the storefront to fetch branding settings.
    """
    settings = db.query(StorefrontSettings).filter(
        StorefrontSettings.user_id == user_id
    ).first()

    if not settings:
        # Return default settings if none exist
        return StorefrontSettingsResponse(
            id=0,
            user_id=user_id,
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
