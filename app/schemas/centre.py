from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.schemas.centre_test import CentreTestResponse, CentreTestCreate


class CentreBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Apollo Diagnostics Indiranagar"])
    address: str = Field(..., min_length=5, examples=["100 Feet Road, HAL 2nd Stage, Indiranagar"])
    city: str = Field(..., min_length=2, max_length=100, examples=["Bengaluru"])
    state: str = Field(..., min_length=2, max_length=100, examples=["Karnataka"])
    pincode: str = Field(..., min_length=4, max_length=20, examples=["560038"])
    phone: Optional[str] = Field(None, examples=["+918025201122"])
    email: Optional[EmailStr] = Field(None, examples=["contact@apollodiagnostics.com"])
    opening_time: str = Field("07:00", examples=["07:00"])
    closing_time: str = Field("20:00", examples=["20:00"])


class CentreCreate(CentreBase):
    tests: Optional[List[CentreTestCreate]] = Field(default=[], description="Initial tests and prices")


class CentreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    is_active: Optional[bool] = None


class CentreResponse(CentreBase):
    id: int
    is_active: bool
    created_at: datetime
    centre_tests: List[CentreTestResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CentreListItemResponse(CentreBase):
    id: int
    is_active: bool
    created_at: datetime
    total_tests_available: int = 0

    model_config = ConfigDict(from_attributes=True)
