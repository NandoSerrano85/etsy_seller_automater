import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from . import model
from . import service
from server.src.database.core import get_db
from server.src.rate_limit import limiter


router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)

@router.post("/register", response_model=model.AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register_user(request: Request, register_user_request: model.RegisterUserRequest, db: Session = Depends(get_db)):
    user = service.register_user(register_user_request, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Registration failed")
    access_token_expires = timedelta(minutes=service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(user.email, user.id, access_token_expires)
    return model.AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=service.create_user_profile(user)
    )

@router.post("/token", response_model=model.AuthResponse)
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # logging.info(form_data)
    return service.login_for_access_token(form_data, db)

@router.get("/verify-token", response_model=model.TokenData)
async def verify_token(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login"))):
    return service.get_current_user(token)