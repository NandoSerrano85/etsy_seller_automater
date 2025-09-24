from fastapi import APIRouter, status, Depends, HTTPException
from uuid import UUID
from typing import List

from sqlalchemy.orm import Session
from server.src.database.core import get_db
from . import model
from . import service
from server.src.routes.auth.service import CurrentUser
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix="/settings",
    tags=["Settings","SizeConfig"]
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="size-config-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

@router.get('/size-config', response_model=List[model.SizeConfigResponse])
async def get_all_size_configs(
        current_user: CurrentUser,
        db: Session = Depends(get_db)
    ):
    """Get all size configs (threaded)"""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    @run_in_thread
    def get_size_configs_threaded():
        return service.get_all_size_configs(user_id, db)

    return await get_size_configs_threaded()
@router.post('/{product_template_id}/{canvas_config_id}/size-config', response_model=model.SizeConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_size_config(
        product_template_id: UUID,
        canvas_config_id: UUID,
        size_config: model.SizeConfigCreate,
        db: Session = Depends(get_db)
    ):
    """Create size config (threaded)"""
    @run_in_thread
    def create_size_config_threaded():
        return service.create_size_config(size_config, product_template_id, canvas_config_id, db)

    return await create_size_config_threaded()

@router.get('/{product_template_id}/{canvas_config_id}/size-config/get-list-with-relations', response_model=List[model.SizeConfigWithRelationsResponse])
async def get_size_configs_with_relations(
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Get size configs with relations (threaded)"""
    @run_in_thread
    def get_size_configs_with_relations_threaded():
        return service.get_size_configs_with_relations(canvas_config_id, product_template_id, db)

    return await get_size_configs_with_relations_threaded()

@router.get('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}', response_model=model.SizeConfigResponse)
async def get_size_config_by_id(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Get size config by ID (threaded)"""
    @run_in_thread
    def get_size_config_by_id_threaded():
        return service.get_size_config_by_id(size_config_id, canvas_config_id, product_template_id, db)

    return await get_size_config_by_id_threaded()

@router.get('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}/with-relations', response_model=model.SizeConfigWithRelationsResponse)
async def get_size_config_by_id_with_relations(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Get size config by ID with relations (threaded)"""
    @run_in_thread
    def get_size_config_by_id_with_relations_threaded():
        return service.get_size_config_by_id_with_relations(size_config_id, canvas_config_id, product_template_id, db)

    return await get_size_config_by_id_with_relations_threaded()

@router.put('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}', response_model=model.SizeConfigResponse)
async def update_size_config(
        size_config: model.SizeConfigUpdate,
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Update size config (threaded)"""
    @run_in_thread
    def update_size_config_threaded():
        return service.update_size_config(size_config, size_config_id, canvas_config_id, product_template_id, db)

    return await update_size_config_threaded()

@router.delete('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_size_config(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    """Delete size config (threaded)"""
    @run_in_thread
    def delete_size_config_threaded():
        return service.delete_size_config(size_config_id, canvas_config_id, product_template_id, db)

    await delete_size_config_threaded()