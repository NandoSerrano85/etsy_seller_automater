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
from server.src.database.core import get_db
from .model import RegisterUserRequest, TokenData, UserToken, UserProfile, AuthResponse, ShopInfo
load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required but not set")

ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')  # Default to HS256 if not set
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
        logging.info(f"Verifying token: {token[:20]}..." if token else "No token provided")
        if not token or len(token.split('.')) != 3:
            logging.error(f"Invalid JWT format: token has {len(token.split('.')) if token else 0} segments, expected 3")
            raise AuthVerifyTokenError(token)
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        logging.info(f"Token verified for user: {user_id}")
        return TokenData(user_id=user_id)
    except PyJWTError as e:
        logging.error(f"JWT decode error: {e}")
        raise AuthVerifyTokenError(token)

def register_user(register_user_request: RegisterUserRequest, db: Session) -> User | bool:
    try:
        # Check if multi-tenant is enabled
        multi_tenant_enabled = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'
        
        if multi_tenant_enabled:
            return register_user_multi_tenant(register_user_request, db)
        else:
            # Legacy single-tenant registration
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
        logging.error(f"Registration failed: {e}")
        return False

def register_user_multi_tenant(register_user_request: RegisterUserRequest, db: Session) -> User | bool:
    """Handle multi-tenant user registration."""
    from server.src.entities.organization import Organization, OrganizationMember
    
    try:
        if register_user_request.registration_mode == 'create':
            # Create new organization
            if not register_user_request.organization_name:
                logging.error("Organization name is required for creating new organization")
                return False
                
            # Create organization
            organization = Organization(
                name=register_user_request.organization_name,
                description=f"Organization for {register_user_request.organization_name}",
                settings={}
            )
            db.add(organization)
            db.flush()  # Get the organization ID
            
            # Create user with organization reference
            user = User(
                email=register_user_request.email,
                hashed_password=get_password_hash(register_user_request.password),
                shop_name=register_user_request.shop_name,
                org_id=organization.id,
                role='owner'  # First user is owner
            )
            db.add(user)
            db.flush()  # Get the user ID
            
            # Create organization membership
            membership = OrganizationMember(
                organization_id=organization.id,
                user_id=user.id,
                role='owner'
            )
            db.add(membership)
            
            db.commit()
            db.refresh(user)
            return user
            
        elif register_user_request.registration_mode == 'join':
            # Join existing organization via invite code
            if not register_user_request.invite_code:
                logging.error("Invite code is required for joining organization")
                return False
            
            # TODO: Implement invite code logic
            # For now, just create user without organization
            user = User(
                email=register_user_request.email,
                hashed_password=get_password_hash(register_user_request.password),
                shop_name=register_user_request.shop_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        else:
            logging.error(f"Invalid registration mode: {register_user_request.registration_mode}")
            return False
            
    except Exception as e:
        logging.error(f"Multi-tenant registration failed: {e}")
        db.rollback()
        return False

def get_current_user(token: Annotated[str, Depends(oath2_bearer)]) -> TokenData:
    return verify_token(token)

def get_current_shop_info(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> ShopInfo:
    """Get the current user's shop information from the database."""
    user_id = current_user.get_uuid()
    if not user_id:
        raise AuthUserNotFound()
    
    # Get user with shop information
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthUserNotFound()
    
    return ShopInfo(
        user_id=user_id,
        shop_id=user.etsy_shop_id,
        shop_name=user.shop_name
    )

CurrentUser = Annotated[TokenData, Depends(get_current_user)]
CurrentShopInfo = Annotated[ShopInfo, Depends(get_current_shop_info)]

def create_user_profile(user: User) -> UserProfile:
    """Create a UserProfile from a User entity."""
    return UserProfile(
        id=user.id,
        email=user.email,
        shop_name=user.shop_name,
        is_active=user.is_active,
        created_at=user.created_at
    )

def get_user_by_token(token: str, db: Session) -> User:
    """Get full user details by token."""
    token_data = verify_token(token)
    user = db.query(User).filter(User.id == token_data.get_uuid()).first()
    if not user:
        raise AuthUserNotFound()
    return user

def login_for_access_token(form_data: OAuth2PasswordRequestForm, db: Session) -> AuthResponse:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise AuthUserNotFound()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, user.id, access_token_expires)
    
    return AuthResponse(
        access_token=access_token, 
        token_type="bearer", 
        expires_in=int(access_token_expires.total_seconds()),
        user=create_user_profile(user)
    )