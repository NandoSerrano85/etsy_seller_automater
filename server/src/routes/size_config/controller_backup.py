from fastapi import APIRouter, status, Depends, HTTPException
from uuid import UUID
from typing import List

from sqlalchemy.orm import Session
from server.src.database.core import get_db
from . import model
from . import service
from server.src.routes.auth.service import CurrentUser

router = APIRouter(
    prefix="/settings",
    tags=["Settings","SizeConfig"]
)

@router.get('/size-config', response_model=List[model.SizeConfigResponse])
async def get_all_size_configs(
        current_user: CurrentUser,
        db: Session = Depends(get_db)
    ):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.get_all_size_configs(user_id, db)
@router.post('/{product_template_id}/{canvas_config_id}/size-config', response_model=model.SizeConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_size_config(
        product_template_id: UUID,
        canvas_config_id: UUID,
        size_config: model.SizeConfigCreate,
        db: Session = Depends(get_db)
    ):
    return service.create_size_config(size_config, product_template_id, canvas_config_id, db)

@router.get('/{product_template_id}/{canvas_config_id}/size-config/get-list-with-relations', response_model=List[model.SizeConfigWithRelationsResponse])
async def get_size_configs_with_relations(
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.get_size_configs_with_relations(canvas_config_id, product_template_id, db)

@router.get('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}', response_model=model.SizeConfigResponse)
async def get_size_config_by_id(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.get_size_config_by_id(size_config_id, canvas_config_id, product_template_id, db)

@router.get('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}/with-relations', response_model=model.SizeConfigWithRelationsResponse)
async def get_size_config_by_id_with_relations(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.get_size_config_by_id_with_relations(size_config_id, canvas_config_id, product_template_id, db)

@router.put('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}', response_model=model.SizeConfigResponse)
async def update_size_config(
        size_config: model.SizeConfigUpdate,
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.update_size_config(size_config, size_config_id, canvas_config_id, product_template_id, db)

@router.delete('/{product_template_id}/{canvas_config_id}/size-config/{size_config_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_size_config(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.delete_size_config(size_config_id, canvas_config_id, product_template_id, db)