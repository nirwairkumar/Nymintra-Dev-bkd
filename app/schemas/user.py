from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    
class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    auth_provider: Optional[str] = "supabase"
    created_at: Optional[datetime] = None
    role: Optional[str] = "user"
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserResponse] = None

class TokenData(BaseModel):
    phone: Optional[str] = None
