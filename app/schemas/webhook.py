from typing import Optional, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.booking import BookingStatus


class PaymentWebhookPayload(BaseModel):
    event_id: str = Field(..., min_length=4, max_length=128, examples=["evt_test_987654321"], description="Unique provider event ID")
    event_type: str = Field("payment.status.updated", examples=["payment.status.updated"])
    transaction_id: str = Field(..., examples=["txn_sim_987654"])
    booking_id: int = Field(..., description="ID of associated booking")
    status: Literal["SUCCESS", "FAILED"] = Field(..., description="Payment status result")
    amount: Decimal = Field(..., gt=0, decimal_places=2, examples=[450.00])
    currency: Optional[str] = Field("INR", examples=["INR"])
    signature: Optional[str] = Field(None, description="Optional HMAC-SHA256 signature header or body field")


class WebhookResponse(BaseModel):
    status: str = Field(..., examples=["processed"])  # "processed" or "already_processed"
    message: str
    event_id: str
    booking_id: Optional[int] = None
    booking_status: Optional[BookingStatus] = None
    is_duplicate: bool = False

    model_config = ConfigDict(from_attributes=True)
