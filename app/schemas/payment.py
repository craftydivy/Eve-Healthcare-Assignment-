from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.payment import PaymentStatus
from app.models.booking import BookingStatus


class PaymentSimulateRequest(BaseModel):
    booking_id: int = Field(..., description="ID of booking to pay for")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Payment amount (must match booking price)")
    payment_method: Optional[Literal["CARD", "UPI", "NETBANKING", "WALLET"]] = Field("CARD", description="Simulated payment method")
    simulate_status: Optional[Literal["SUCCESS", "FAILED"]] = Field("SUCCESS", description="Choose simulated outcome: SUCCESS or FAILED")
    idempotency_key: Optional[str] = Field(None, max_length=120, description="Optional client idempotency key to prevent double charging")


class PaymentResponse(BaseModel):
    transaction_id: str
    booking_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: str
    gateway_reference: Optional[str] = None
    booking_status: BookingStatus
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
