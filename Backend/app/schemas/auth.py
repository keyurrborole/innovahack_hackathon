"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime


class LoginRequest(BaseModel):
    code: str
    provider: Literal["google", "github"]


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    createdAt: Optional[datetime] = None


class TokenResponse(BaseModel):
    token: str
    refreshToken: Optional[str] = None
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class RefreshTokenRequest(BaseModel):
    refreshToken: str
