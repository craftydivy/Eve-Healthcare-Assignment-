import logging
from typing import Dict, Any

logger = logging.getLogger("eve_healthcare")


def send_booking_confirmation_notification(booking_data: Dict[str, Any]):
    """Simulates sending an email and SMS confirmation for a booked diagnostic test."""
    logger.info(
        f"[NOTIFICATION] Booking Confirmed! Ref: {booking_data.get('booking_ref')}, "
        f"Patient: {booking_data.get('patient_name')}, Centre: {booking_data.get('centre_name')}, "
        f"Test: {booking_data.get('test_name')}, Amount: INR {booking_data.get('amount')}, "
        f"Time: {booking_data.get('appointment_time')}"
    )


def send_payment_receipt_notification(payment_data: Dict[str, Any]):
    """Simulates sending a payment receipt via email."""
    logger.info(
        f"[NOTIFICATION] Payment Receipt Dispatched: Txn: {payment_data.get('transaction_id')}, "
        f"Booking: {payment_data.get('booking_id')}, Amount: {payment_data.get('amount')} {payment_data.get('currency')}, "
        f"Status: {payment_data.get('status')}"
    )
