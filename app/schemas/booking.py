from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.booking import BookingStatus
from app.schemas.centre import CentreResponse
from app.schemas.test import TestResponse


class BookingCreate(BaseModel):
    centre_id: int = Field(..., description="Target diagnostic centre ID")
    test_id: int = Field(..., description="Target diagnostic test ID")
    appointment_time: datetime = Field(..., description="Scheduled appointment datetime (ISO 8601)")
    patient_name: str = Field(..., min_length=2, max_length=150, examples=["Priya Sharma"])
    patient_age: Optional[int] = Field(None, ge=0, le=125, examples=[28])
    patient_gender: Optional[str] = Field("Female", examples=["Female"])
    patient_phone: Optional[str] = Field(None, examples=["+919876543210"])
    notes: Optional[str] = Field(None, examples=["Special assistance needed: wheelchair"])

    @field_validator("appointment_time")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        target = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if target <= now:
            raise ValueError("Appointment time must be in the future")
        return v


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = Field(..., description="New booking status")
    notes: Optional[str] = Field(None, description="Reason or note for status update")


class BookingResponse(BaseModel):
    id: int
    booking_ref: str
    user_id: int
    centre_id: int
    test_id: int
    appointment_time: datetime
    amount: Decimal
    currency: str
    status: BookingStatus
    patient_name: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    centre: Optional[CentreResponse] = None
    test: Optional[TestResponse] = None

    model_config = ConfigDict(from_attributes=True)
