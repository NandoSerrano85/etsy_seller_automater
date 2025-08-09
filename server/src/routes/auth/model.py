from pydantic import BaseModel, EmailStr
from uuid import UUID


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str
    shop_name: str

class UserToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    user_id: str | None = None
    def get_uuid(self) -> UUID | None:
        if self.user_id:
            return UUID(self.user_id)
        return None

class TokenDataRequest(BaseModel):
    token:str  