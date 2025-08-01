from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from jwt import PyJWTError
from server.src.message import AuthVerifyTokenError, AuthUserNotFound
import os, jwt, logging

from server.src.entities.user import User
from .model import RegisterUserRequest, TokenData, UserToken
load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = os.getenv('JWT_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('USER_LOGIN_ACCESS_TOKEN_EXPIRE_MINUTES', 30))

oath2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return bcrypt_context.hash(password)

def create_access_token(email: str, user_id: UUID, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    to_encode = {
        "sub": email,
        "id": str(user_id),
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(email: str, password: str, db: Session) -> User | bool:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        return TokenData(user_id=user_id)
    except PyJWTError as e:
        logging.error(e)
        raise AuthVerifyTokenError(token)

def register_user(register_user_request: RegisterUserRequest, db: Session) -> User | bool:
    try:
        user = User(
            email=register_user_request.email,
            hashed_password=get_password_hash(register_user_request.password),
            shop_name=register_user_request.shop_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        logging.error(e)
        return False

def get_current_user(token: Annotated[str, Depends(oath2_bearer)]) -> TokenData:
    return verify_token(token)

CurrentUser = Annotated[TokenData, Depends(get_current_user)]

def login_for_access_token(form_data: OAuth2PasswordRequestForm, db: Session) -> UserToken:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise AuthUserNotFound()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, user.id, access_token_expires)
    return UserToken(access_token=access_token, token_type="bearer", expires_in=int(access_token_expires.total_seconds()))