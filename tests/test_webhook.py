import uuid
from datetime import datetime, timezone, timedelta
from fastapi import status
from app.models.payment import Payment


def _create_pending_booking(client, headers, centre_id, test_id):
    future_time = datetime.now(timezone.utc) + timedelta(days=3)
    res = client.post("/api/v1/bookings/", headers=headers, json={
        "centre_id": centre_id,
        "test_id": test_id,
        "appointment_time": future_time.isoformat(),
        "patient_name": "Webhook Test Patient",
    })
    assert res.status_code == status.HTTP_201_CREATED
    return res.json()


def test_webhook_success_updates_booking(client, test_users, sample_centre_and_test, db_session):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    event_id = f"evt_test_{uuid.uuid4().hex[:8]}"
    webhook_payload = {
        "event_id": event_id,
        "event_type": "payment.status.updated",
        "transaction_id": "txn_wh_001",
        "booking_id": booking["id"],
        "status": "SUCCESS",
        "amount": booking["amount"],
        "currency": "INR"
    }

    response = client.post("/api/v1/payments/webhook/", json=webhook_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "processed"
    assert data["is_duplicate"] is False
    assert data["booking_status"] == "CONFIRMED"

    # Verify booking status
    booking_check = client.get(f"/api/v1/bookings/{booking['id']}", headers=headers)
    assert booking_check.json()["status"] == "CONFIRMED"


def test_webhook_strict_idempotency_duplicate_events(client, test_users, sample_centre_and_test, db_session):
    """
    CRITICAL REQUIREMENT TEST:
    If the same webhook/event is received multiple times, it must not create duplicate
    payments, duplicate bookings, or otherwise corrupt the booking state.
    """
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    event_id = f"evt_strict_idemp_{uuid.uuid4().hex[:8]}"
    webhook_payload = {
        "event_id": event_id,
        "event_type": "payment.status.updated",
        "transaction_id": "txn_wh_idemp_002",
        "booking_id": booking["id"],
        "status": "SUCCESS",
        "amount": booking["amount"],
        "currency": "INR"
    }

    # 1st execution: processed
    res1 = client.post("/api/v1/payments/webhook/", json=webhook_payload)
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["status"] == "processed"
    assert res1.json()["is_duplicate"] is False

    # Count payments for this booking
    payments_count_1 = db_session.query(Payment).filter(Payment.booking_id == booking["id"]).count()
    assert payments_count_1 == 1

    # 2nd execution (exact duplicate event): must be identified as duplicate and skipped
    res2 = client.post("/api/v1/payments/webhook/", json=webhook_payload)
    assert res2.status_code == status.HTTP_200_OK
    assert res2.json()["status"] == "already_processed"
    assert res2.json()["is_duplicate"] is True

    # 3rd execution (triple hit from network replay)
    res3 = client.post("/api/v1/payments/webhook/", json=webhook_payload)
    assert res3.status_code == status.HTTP_200_OK
    assert res3.json()["status"] == "already_processed"
    assert res3.json()["is_duplicate"] is True

    # Payments count MUST STILL BE 1 - zero duplicate records created!
    payments_count_after = db_session.query(Payment).filter(Payment.booking_id == booking["id"]).count()
    assert payments_count_after == 1

    # Booking state is uncorrupted
    booking_check = client.get(f"/api/v1/bookings/{booking['id']}", headers=headers)
    assert booking_check.json()["status"] == "CONFIRMED"


def test_webhook_failure_transitions_to_failed(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    event_id = f"evt_fail_{uuid.uuid4().hex[:8]}"
    webhook_payload = {
        "event_id": event_id,
        "event_type": "payment.status.updated",
        "transaction_id": "txn_wh_fail_003",
        "booking_id": booking["id"],
        "status": "FAILED",
        "amount": booking["amount"],
    }

    res = client.post("/api/v1/payments/webhook/", json=webhook_payload)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["booking_status"] == "FAILED"

    booking_check = client.get(f"/api/v1/bookings/{booking['id']}", headers=headers)
    assert booking_check.json()["status"] == "FAILED"


def test_webhook_out_of_order_failure_does_not_corrupt_confirmed_booking(client, test_users, sample_centre_and_test):
    """If a booking is already CONFIRMED, an out-of-order FAILED webhook does not corrupt it."""
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    # First event: Success
    res_success = client.post("/api/v1/payments/webhook/", json={
        "event_id": f"evt_order1_{uuid.uuid4().hex[:8]}",
        "transaction_id": "txn_success",
        "booking_id": booking["id"],
        "status": "SUCCESS",
        "amount": booking["amount"],
    })
    assert res_success.status_code == status.HTTP_200_OK

    # Out of order failure event arrives
    res_failed = client.post("/api/v1/payments/webhook/", json={
        "event_id": f"evt_order2_{uuid.uuid4().hex[:8]}",
        "transaction_id": "txn_delayed_fail",
        "booking_id": booking["id"],
        "status": "FAILED",
        "amount": booking["amount"],
    })
    assert res_failed.status_code == status.HTTP_200_OK

    # Booking must REMAIN CONFIRMED
    booking_check = client.get(f"/api/v1/bookings/{booking['id']}", headers=headers)
    assert booking_check.json()["status"] == "CONFIRMED"


def test_webhook_invalid_booking_id(client):
    res = client.post("/api/v1/payments/webhook/", json={
        "event_id": f"evt_invalid_{uuid.uuid4().hex[:8]}",
        "transaction_id": "txn_invalid",
        "booking_id": 999999,
        "status": "SUCCESS",
        "amount": 500.00,
    })
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_webhook_amount_mismatch(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    res = client.post("/api/v1/payments/webhook/", json={
        "event_id": f"evt_mismatch_{uuid.uuid4().hex[:8]}",
        "transaction_id": "txn_mismatch",
        "booking_id": booking["id"],
        "status": "SUCCESS",
        "amount": 99999.00,  # Incorrect amount
    })
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "mismatch" in res.json()["detail"]
