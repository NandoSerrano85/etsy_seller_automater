from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from . import model
from . import service

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

@router.get('/me', response_model=model.UserResponse)
async def get_current_user(current_user: CurrentUser, db: Session = Depends(get_db)):
    return service.get_user_by_id(db, current_user.get_uuid())

@router.put('/change-password', status_code=status.HTTP_200_OK)
async def change_passwordr(password_change: model.PasswordChangeRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    service.change_password(db, current_user.get_uuid(), password_change)