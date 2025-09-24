from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from server.src.database.core import get_db
from . import model
from . import service
from server.src.routes.auth.service import CurrentUser
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix="/settings",
    tags=["Settings", "CanvasConfig"]
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="canvas-sizes-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper
@router.get('/canvas-config', response_model=List[model.CanvasConfigResponse])
async def get_all_canvas_configs(
        current_user: CurrentUser,
        db: Session = Depends(get_db)
    ):
    """Get all canvas configs (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_canvas_configs_threaded():
        return service.get_all_canvas_configs(user_id, db)

    return await get_canvas_configs_threaded()

@router.post('/{product_template_id}/canvas-config', response_model=model.CanvasConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_canvas_config(
        product_template_id: UUID,
        canvas_config: model.CanvasConfigCreate,
        db: Session = Depends(get_db)
    ):
    """Create canvas config (threaded)"""
    @run_in_thread
    def create_canvas_config_threaded():
        return service.create_canvas_config(canvas_config, product_template_id, db)

    return await create_canvas_config_threaded()

@router.get('/{product_template_id}/canvas-config/{canvas_config_id}', response_model=model.CanvasConfigResponse)
async def get_canvas_config_by_id(
        product_template_id: UUID,
        canvas_config_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Get canvas config by ID (threaded)"""
    @run_in_thread
    def get_canvas_config_threaded():
        return service.get_canvas_config_by_id(canvas_config_id, product_template_id, db)

    return await get_canvas_config_threaded()

@router.put('/{product_template_id}/canvas-config/{canvas_config_id}', response_model=model.CanvasConfigResponse)
async def update_canvas_config_by_id(
        product_template_id: UUID,
        canvas_config: model.CanvasConfigUpdate,
        canvas_config_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Update canvas config (threaded)"""
    @run_in_thread
    def update_canvas_config_threaded():
        return service.update_canvas_config(canvas_config, canvas_config_id, product_template_id, db)

    return await update_canvas_config_threaded()

@router.delete('/{product_template_id}/canvas-config/{canvas_config_id}', status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_canvas_config_by_id(
        product_template_id: UUID,
        canvas_config_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Delete canvas config (threaded)"""
    @run_in_thread
    def delete_canvas_config_threaded():
        return service.delete_canvas_config(canvas_config_id, product_template_id, db)

    await delete_canvas_config_threaded()