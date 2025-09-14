from fastapi import APIRouter, status, Depends, HTTPException, Query
from uuid import UUID
from typing import List

from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from .model import (
    TemplateEditorCreate,
    TemplateEditorUpdate,
    TemplateEditorResponse,
    TemplatePreview,
    TemplatePreviewResponse,
    TemplateListResponse
)
from .service import TemplateEditorService

router = APIRouter(
    prefix="/templates",
    tags=["Template Editor"]
)

@router.post("/", response_model=TemplateEditorResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateEditorCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new template with background and design areas"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    service = TemplateEditorService(db)
    return service.create_template(template_data, user_id)

@router.get("/", response_model=TemplateListResponse)
async def get_templates(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get user's templates"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    service = TemplateEditorService(db)
    templates = service.get_templates(user_id, page, per_page)

    return TemplateListResponse(
        templates=templates,
        total=len(templates),  # TODO: Get actual count
        page=page,
        per_page=per_page
    )

@router.get("/{template_id}", response_model=TemplateEditorResponse)
async def get_template_by_id(
    template_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get specific template by ID"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    service = TemplateEditorService(db)
    return service.get_template_by_id(template_id, user_id)

@router.put("/{template_id}", response_model=TemplateEditorResponse)
async def update_template(
    template_id: UUID,
    template_data: TemplateEditorUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update existing template"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    service = TemplateEditorService(db)
    return service.update_template(template_id, template_data, user_id)

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete template"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    service = TemplateEditorService(db)
    return service.delete_template(template_id, user_id)

@router.post("/preview", response_model=TemplatePreviewResponse)
async def generate_template_preview(
    preview_data: TemplatePreview,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Generate preview with design overlay"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    service = TemplateEditorService(db)
    return service.generate_preview(preview_data, user_id)