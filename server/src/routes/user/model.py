from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    shop_name: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str