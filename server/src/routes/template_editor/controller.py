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
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix="/templates",
    tags=["Template Editor"]
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="template-editor-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

@router.post("/", response_model=TemplateEditorResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateEditorCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new template with background and design areas (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def create_template_threaded():
        service = TemplateEditorService(db)
        return service.create_template(template_data, user_id)

    return await create_template_threaded()

@router.get("/", response_model=TemplateListResponse)
async def get_templates(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get user's templates (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_templates_threaded():
        service = TemplateEditorService(db)
        templates = service.get_templates(user_id, page, per_page)
        return TemplateListResponse(
            templates=templates,
            total=len(templates),  # TODO: Get actual count
            page=page,
            per_page=per_page
        )

    return await get_templates_threaded()

@router.get("/{template_id}", response_model=TemplateEditorResponse)
async def get_template_by_id(
    template_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get specific template by ID (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_template_by_id_threaded():
        service = TemplateEditorService(db)
        return service.get_template_by_id(template_id, user_id)

    return await get_template_by_id_threaded()

@router.put("/{template_id}", response_model=TemplateEditorResponse)
async def update_template(
    template_id: UUID,
    template_data: TemplateEditorUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update existing template (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def update_template_threaded():
        service = TemplateEditorService(db)
        return service.update_template(template_id, template_data, user_id)

    return await update_template_threaded()

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete template (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def delete_template_threaded():
        service = TemplateEditorService(db)
        return service.delete_template(template_id, user_id)

    await delete_template_threaded()

@router.post("/preview", response_model=TemplatePreviewResponse)
async def generate_template_preview(
    preview_data: TemplatePreview,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Generate preview with design overlay (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def generate_template_preview_threaded():
        service = TemplateEditorService(db)
        return service.generate_preview(preview_data, user_id)

    return await generate_template_preview_threaded()