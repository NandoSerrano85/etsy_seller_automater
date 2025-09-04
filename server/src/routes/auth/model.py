from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str
    shop_name: str

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    shop_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserProfile

class TokenData(BaseModel):
    user_id: str | None = None
    def get_uuid(self) -> UUID | None:
        if self.user_id:
            return UUID(self.user_id)
        return None

class TokenDataRequest(BaseModel):
    token:str  