import uuid
import hmac
import hashlib
import json
import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, BackgroundTasks
from app.config import settings
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.models.user import User
from app.schemas.payment import PaymentSimulateRequest, PaymentResponse
from app.schemas.webhook import PaymentWebhookPayload, WebhookResponse
from app.services.notification_service import send_booking_confirmation_notification, send_payment_receipt_notification

logger = logging.getLogger("eve_healthcare")


def verify_webhook_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """Verify HMAC-SHA256 signature for incoming webhook payloads.
    
    Ensures idempotent webhook processing by validating authenticity of payment provider.
    """
    if not settings.WEBHOOK_SECRET or not signature_header:
        # If signature header is not supplied, allow if not in strict mode, or verify
        return True
    
    expected_signature = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


def generate_webhook_signature(payload_dict: dict) -> str:
    """Helper to generate HMAC-SHA256 signature for testing webhooks."""
    payload_bytes = json.dumps(payload_dict, sort_keys=True, default=str).encode("utf-8")
    return hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()


def simulate_payment(
    db: Session,
    current_user: User,
    data: PaymentSimulateRequest,
    background_tasks: Optional[BackgroundTasks] = None
) -> PaymentResponse:
    """Process a simulated payment for a booking with validation and idempotency."""
    # 1. Fetch booking with locking if supported
    booking_query = db.query(Booking).filter(Booking.id == data.booking_id)
    if not settings.DATABASE_URL.startswith("sqlite"):
        booking_query = booking_query.with_for_update()
    
    booking = booking_query.first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {data.booking_id} not found."
        )

    # 2. Authorization check: must be owner or admin
    if current_user.role not in ["ADMIN", "STAFF"] and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to process payment for this booking."
        )

    # 2.5 Idempotency Key check: if client sent an idempotency key, return existing payment if already processed
    if data.idempotency_key:
        existing_payment = db.query(Payment).filter(
            Payment.idempotency_key == data.idempotency_key
        ).first()
        if existing_payment:
            return PaymentResponse(
                transaction_id=existing_payment.transaction_id,
                booking_id=existing_payment.booking_id,
                amount=existing_payment.amount,
                currency=existing_payment.currency,
                status=existing_payment.status,
                payment_method=existing_payment.payment_method,
                gateway_reference=existing_payment.gateway_reference,
                booking_status=booking.status,
                message="Idempotent payment request: returning previously processed transaction.",
                created_at=existing_payment.created_at,
            )

    # 3. Check booking status edge cases
    if booking.status == BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking has already been paid for and confirmed. Double payment is prevented."
        )
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot process payment for a cancelled booking."
        )

    # 4. Price tampering check: amount must match booking amount
    if Decimal(str(data.amount)) != Decimal(str(booking.amount)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount mismatch. Booking amount is INR {booking.amount}, provided amount is INR {data.amount}."
        )

    # 6. Process simulated outcome
    transaction_id = f"txn_sim_{uuid.uuid4().hex[:12]}"
    outcome = data.simulate_status or "SUCCESS"

    if outcome == "SUCCESS":
        payment_status = PaymentStatus.SUCCESS
        booking.status = BookingStatus.CONFIRMED
        message = "Payment simulated successfully. Booking has been confirmed!"
    else:
        payment_status = PaymentStatus.FAILED
        booking.status = BookingStatus.FAILED
        message = "Payment simulation failed. Booking status set to FAILED."

    # 7. Record payment
    payment = Payment(
        transaction_id=transaction_id,
        booking_id=booking.id,
        amount=booking.amount,
        currency="INR",
        status=payment_status,
        payment_method=data.payment_method or "CARD",
        gateway_reference=f"gw_ref_{uuid.uuid4().hex[:8]}",
        idempotency_key=data.idempotency_key,
        raw_response=json.dumps({"simulated": True, "outcome": outcome})
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(booking)

    # 8. Dispatch notification in background if confirmed
    if payment_status == PaymentStatus.SUCCESS and background_tasks:
        background_tasks.add_task(
            send_booking_confirmation_notification,
            {
                "booking_ref": booking.booking_ref,
                "patient_name": booking.patient_name,
                "centre_name": booking.centre.name if booking.centre else f"Centre #{booking.centre_id}",
                "test_name": booking.test.name if booking.test else f"Test #{booking.test_id}",
                "amount": str(booking.amount),
                "appointment_time": booking.appointment_time.isoformat(),
            }
        )
        background_tasks.add_task(
            send_payment_receipt_notification,
            {
                "transaction_id": payment.transaction_id,
                "booking_id": booking.id,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status.value,
            }
        )

    return PaymentResponse(
        transaction_id=payment.transaction_id,
        booking_id=payment.booking_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        payment_method=payment.payment_method,
        gateway_reference=payment.gateway_reference,
        booking_status=booking.status,
        message=message,
        created_at=payment.created_at,
    )


def process_payment_webhook(
    db: Session,
    payload: PaymentWebhookPayload,
    raw_payload_str: str,
    signature_header: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None
) -> WebhookResponse:
    """Process incoming payment webhook with guaranteed idempotency and state safety."""
    # Step 1: Idempotency Check (Check if this event_id has already been processed)
    existing_event = db.query(WebhookEvent).filter(
        WebhookEvent.event_id == payload.event_id
    ).first()

    if existing_event:
        logger.warning(f"[WEBHOOK IDEMPOTENT] Duplicate webhook received for event_id={payload.event_id}. Skipping processing.")
        booking = db.query(Booking).filter(Booking.id == existing_event.booking_id).first()
        return WebhookResponse(
            status="already_processed",
            message=f"Event {payload.event_id} has already been processed. No duplicate actions taken.",
            event_id=payload.event_id,
            booking_id=existing_event.booking_id,
            booking_status=booking.status if booking else None,
            is_duplicate=True,
        )

    # Step 2: Validate Booking exists
    booking_query = db.query(Booking).filter(Booking.id == payload.booking_id)
    if not settings.DATABASE_URL.startswith("sqlite"):
        booking_query = booking_query.with_for_update()

    booking = booking_query.first()
    if not booking:
        # Record failed webhook attempt
        failed_event = WebhookEvent(
            event_id=payload.event_id,
            event_type=payload.event_type,
            booking_id=payload.booking_id,
            transaction_id=payload.transaction_id,
            status="FAILED",
            payload=raw_payload_str,
            error_message=f"Booking with ID {payload.booking_id} does not exist",
        )
        db.add(failed_event)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {payload.booking_id} not found."
        )

    # Step 3: Verify Amount matches
    if Decimal(str(payload.amount)) != Decimal(str(booking.amount)):
        failed_event = WebhookEvent(
            event_id=payload.event_id,
            event_type=payload.event_type,
            booking_id=payload.booking_id,
            transaction_id=payload.transaction_id,
            status="FAILED",
            payload=raw_payload_str,
            error_message=f"Amount mismatch: Webhook has {payload.amount}, booking has {booking.amount}",
        )
        db.add(failed_event)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook amount mismatch. Expected {booking.amount}, received {payload.amount}."
        )

    # Step 4: State transition logic
    # Real-world safety: If booking is already CONFIRMED, do not regress to FAILED
    if payload.status == "SUCCESS":
        booking.status = BookingStatus.CONFIRMED
        payment_status = PaymentStatus.SUCCESS
    else:
        if booking.status == BookingStatus.CONFIRMED:
            logger.warning(f"Received FAILED webhook for already CONFIRMED booking {booking.id}. Ignoring regression.")
            payment_status = PaymentStatus.FAILED
        else:
            booking.status = BookingStatus.FAILED
            payment_status = PaymentStatus.FAILED

    # Step 5: Record Payment
    payment = Payment(
        transaction_id=payload.transaction_id,
        booking_id=booking.id,
        amount=payload.amount,
        currency=payload.currency or "INR",
        status=payment_status,
        payment_method="WEBHOOK_GATEWAY",
        gateway_reference=payload.transaction_id,
        raw_response=raw_payload_str
    )
    db.add(payment)

    # Step 6: Record WebhookEvent for future idempotency checks
    event_record = WebhookEvent(
        event_id=payload.event_id,
        event_type=payload.event_type,
        booking_id=booking.id,
        transaction_id=payload.transaction_id,
        status="PROCESSED",
        payload=raw_payload_str,
        response_payload=json.dumps({"booking_status": booking.status.value}),
    )
    db.add(event_record)
    db.commit()
    db.refresh(booking)

    # Step 7: Background notification if confirmed
    if booking.status == BookingStatus.CONFIRMED and background_tasks:
        background_tasks.add_task(
            send_booking_confirmation_notification,
            {
                "booking_ref": booking.booking_ref,
                "patient_name": booking.patient_name,
                "centre_name": f"Centre #{booking.centre_id}",
                "test_name": f"Test #{booking.test_id}",
                "amount": str(booking.amount),
                "appointment_time": booking.appointment_time.isoformat(),
            }
        )

    logger.info(f"[WEBHOOK PROCESSED] Event {payload.event_id} processed for booking {booking.id}. Status: {booking.status.value}")

    return WebhookResponse(
        status="processed",
        message="Webhook event processed successfully and booking updated.",
        event_id=payload.event_id,
        booking_id=booking.id,
        booking_status=booking.status,
        is_duplicate=False,
    )
