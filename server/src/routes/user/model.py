from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    shop_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str