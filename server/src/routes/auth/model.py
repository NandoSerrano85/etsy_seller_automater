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

class ShopInfo(BaseModel):
    user_id: UUID
    shop_id: str | None = None
    shop_name: str | None = None
    
    def has_shop_id(self) -> bool:
        """Check if shop ID is available."""
        return self.shop_id is not None and self.shop_id != ""
    
    def has_shop_name(self) -> bool:
        """Check if shop name is available.""" 
        return self.shop_name is not None and self.shop_name != ""  