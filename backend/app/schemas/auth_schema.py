from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    confirm_password: str
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str