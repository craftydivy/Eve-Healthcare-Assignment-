from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.test import TestResponse


class CentreTestCreate(BaseModel):
    test_id: int = Field(..., description="ID of diagnostic test to offer")
    price: Decimal = Field(..., gt=0, decimal_places=2, examples=[450.00])
    turnaround_hours: int = Field(24, ge=1, le=168, examples=[24])
    is_available: bool = True


class CentreTestUpdate(BaseModel):
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    turnaround_hours: Optional[int] = Field(None, ge=1, le=168)
    is_available: Optional[bool] = None


class CentreTestResponse(BaseModel):
    id: int
    centre_id: int
    test_id: int
    price: Decimal
    turnaround_hours: int
    is_available: bool
    test: Optional[TestResponse] = None

    model_config = ConfigDict(from_attributes=True)
