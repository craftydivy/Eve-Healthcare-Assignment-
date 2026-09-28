from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TestBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Complete Blood Count (CBC)"])
    code: str = Field(..., min_length=2, max_length=50, examples=["CBC-01"])
    category: str = Field(..., min_length=2, max_length=100, examples=["Pathology"])
    description: Optional[str] = Field(None, examples=["Evaluates overall health and detects anemia, infection, and leukemia."])
    sample_type: Optional[str] = Field("Blood", examples=["Blood"])
    preparation_instructions: Optional[str] = Field(None, examples=["Fasting for 8-10 hours is recommended."])


class TestCreate(TestBase):
    pass


class TestUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    sample_type: Optional[str] = None
    preparation_instructions: Optional[str] = None
    is_active: Optional[bool] = None


class TestResponse(TestBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
