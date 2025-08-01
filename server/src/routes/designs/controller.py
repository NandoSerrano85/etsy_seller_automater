from fastapi import APIRouter, status, Query, HTTPException, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.message import InvalidUserToken
from . import model
from . import service

router = APIRouter(
    prefix='/designs',
    tags=['Designs']
)

@router.post('/', response_model=model.DesignImageResponse, status_code=status.HTTP_201_CREATED)
async def create_design(
    design_data: model.DesignImageCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new design for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.create_design(db, user_id, design_data)

@router.get('/list', response_model=model.DesignImageListResponse)
async def get_designs(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of designs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of designs to return")
):
    """Get all designs for the current user with pagination"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_designs_by_user_id(db, user_id, skip, limit)

@router.get('/by-id/{design_id}', response_model=model.DesignImageResponse)
async def get_design(
    design_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific design by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_design_by_id(db, design_id, user_id)

@router.put('/update/{design_id}', response_model=model.DesignImageResponse)
async def update_design(
    design_id: UUID,
    design_data: model.DesignImageUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a specific design by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.update_design(db, design_id, user_id, design_data)

@router.delete('/delete/{design_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_design(
    design_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a specific design by ID for the current user (soft delete)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    service.delete_design(db, design_id, user_id)
