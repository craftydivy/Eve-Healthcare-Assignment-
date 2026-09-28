from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentSimulateRequest, PaymentResponse
from app.schemas.webhook import PaymentWebhookPayload, WebhookResponse
from app.services.payment_service import (
    simulate_payment,
    process_payment_webhook,
    generate_webhook_signature,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_200_OK, summary="Simulate Payment Processing")
def process_simulated_payment(
    payment_in: PaymentSimulateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simulate payment processing for a booking.
    - Result is either **SUCCESS** or **FAILED** based on input/simulation
    - Updates related booking to **CONFIRMED** (on SUCCESS) or **FAILED** (on FAILED)
    - Prevents double payment if booking is already confirmed
    - Verifies amount matches booking price
    - Dispatches asynchronous confirmation notifications upon success
    """
    response = simulate_payment(
        db=db,
        current_user=current_user,
        data=payment_in,
        background_tasks=background_tasks
    )
    return response


@router.post("/webhook/", response_model=WebhookResponse, summary="Payment Provider Webhook (Idempotent)")
async def payment_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_eve_signature: Optional[str] = Header(None, alias="X-Eve-Signature"),
):
    """
    Receive asynchronous payment-status updates from simulated payment provider.
    
    **CRITICAL IDEMPOTENCY GUARANTEE:**
    - Receiving the same webhook event multiple times will **NOT** create duplicate payments
    - Will **NOT** duplicate bookings or corrupt booking state
    - Safely returns `already_processed` with cached/saved state on duplicate calls
    """
    body_bytes = await request.body()
    body_json = await request.json()
    
    payload = PaymentWebhookPayload(**body_json)
    
    response = process_payment_webhook(
        db=db,
        payload=payload,
        raw_payload_str=body_bytes.decode("utf-8"),
        signature_header=x_eve_signature or payload.signature,
        background_tasks=background_tasks
    )
    return response


@router.post("/webhook/test-signature", summary="Generate HMAC Signature for Webhook Testing")
def test_signature(payload: dict):
    """
    Helper utility to generate HMAC-SHA256 signature for testing secure webhooks.
    """
    sig = generate_webhook_signature(payload)
    return {"signature": sig, "header": f"X-Eve-Signature: {sig}"}
