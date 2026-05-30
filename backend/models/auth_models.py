from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TOTPVerifyRequest(BaseModel):
    session_temp: str
    code: str


class TOTPConfirmRequest(BaseModel):
    code: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    role: str
    totp_enabled: bool
    is_active: bool
    is_banned: bool
    monthly_token_limit: Optional[int] = None
    tokens_used_month: Optional[int] = None