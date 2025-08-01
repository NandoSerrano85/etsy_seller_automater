from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from server.src.database.core import get_db
from . import model
from . import service
from server.src.routes.auth.service import CurrentUser

router = APIRouter(
    prefix="/settings",
    tags=["Settings", "CanvasConfig"]
)
@router.get('/canvas-config', response_model=List[model.CanvasConfigResponse])
async def get_all_canvas_configs(
        current_user: CurrentUser,
        db: Session = Depends(get_db)
    ):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return service.get_all_canvas_configs(user_id, db)

@router.post('/{product_template_id}/canvas-config', response_model=model.CanvasConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_canvas_config(
        product_template_id: UUID,
        canvas_config: model.CanvasConfigCreate,
        db: Session = Depends(get_db)
    ):
    return service.create_canvas_config(canvas_config, product_template_id, db)

@router.get('/{product_template_id}/canvas-config/{canvas_config_id}', response_model=model.CanvasConfigResponse)
async def get_canvas_config_by_id(
        product_template_id: UUID,
        canvas_config_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.get_canvas_config_by_id(canvas_config_id, product_template_id, db)

@router.put('/{product_template_id}/canvas-config/{canvas_config_id}', response_model=model.CanvasConfigResponse)
async def update_canvas_config_by_id(
        product_template_id: UUID,
        canvas_config: model.CanvasConfigUpdate,
        canvas_config_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.update_canvas_config(canvas_config, canvas_config_id, product_template_id, db)

@router.delete('/{product_template_id}/canvas-config/{canvas_config_id}', status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_canvas_config_by_id(
        product_template_id: UUID,
        canvas_config_id: UUID,
        db: Session = Depends(get_db)
    ):
    return service.delete_canvas_config(canvas_config_id, product_template_id, db)