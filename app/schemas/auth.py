from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserSignup(BaseModel):
    email: EmailStr = Field(..., examples=["patient@example.com"])
    password: str = Field(..., min_length=6, max_length=100, examples=["SecurePass123!"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Aarav Sharma"])
    phone: Optional[str] = Field(None, examples=["+919876543210"])
    role: Optional[str] = Field("PATIENT", description="PATIENT or ADMIN")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["patient@example.com"])
    password: str = Field(..., examples=["SecurePass123!"])


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
