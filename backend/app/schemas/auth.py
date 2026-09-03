from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.support_agent


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None
