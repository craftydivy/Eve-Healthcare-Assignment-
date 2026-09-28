from datetime import datetime, timezone, timedelta
from fastapi import status


def _create_pending_booking(client, headers, centre_id, test_id):
    future_time = datetime.now(timezone.utc) + timedelta(days=2, hours=1)
    res = client.post("/api/v1/bookings/", headers=headers, json={
        "centre_id": centre_id,
        "test_id": test_id,
        "appointment_time": future_time.isoformat(),
        "patient_name": "Payment Test Patient",
    })
    assert res.status_code == status.HTTP_201_CREATED
    return res.json()


def test_simulate_payment_success(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    # Process simulated payment
    pay_res = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": booking["amount"],
        "payment_method": "UPI",
        "simulate_status": "SUCCESS"
    })
    assert pay_res.status_code == status.HTTP_200_OK
    pay_data = pay_res.json()
    assert pay_data["status"] == "SUCCESS"
    assert pay_data["booking_status"] == "CONFIRMED"
    assert pay_data["transaction_id"].startswith("txn_sim_")

    # Verify booking status changed to CONFIRMED
    booking_check = client.get(f"/api/v1/bookings/{booking['id']}", headers=headers)
    assert booking_check.json()["status"] == "CONFIRMED"


def test_simulate_payment_failure(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    pay_res = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": booking["amount"],
        "payment_method": "CARD",
        "simulate_status": "FAILED"
    })
    assert pay_res.status_code == status.HTTP_200_OK
    pay_data = pay_res.json()
    assert pay_data["status"] == "FAILED"
    assert pay_data["booking_status"] == "FAILED"

    # Verify booking status changed to FAILED
    booking_check = client.get(f"/api/v1/bookings/{booking['id']}", headers=headers)
    assert booking_check.json()["status"] == "FAILED"


def test_prevent_double_payment_on_confirmed_booking(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    # First payment: Success
    res1 = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": booking["amount"],
        "simulate_status": "SUCCESS"
    })
    assert res1.status_code == status.HTTP_200_OK

    # Second payment: Double payment prevented
    res2 = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": booking["amount"],
        "simulate_status": "SUCCESS"
    })
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "Double payment is prevented" in res2.json()["detail"]


def test_payment_amount_mismatch_rejection(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    # Send incorrect amount (e.g. 10.00 instead of 500.00)
    pay_res = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": 10.00,
        "simulate_status": "SUCCESS"
    })
    assert pay_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "mismatch" in pay_res.json()["detail"]


def test_payment_idempotency_key(client, test_users, sample_centre_and_test):
    headers = test_users["patient1_headers"]
    booking = _create_pending_booking(client, headers, sample_centre_and_test["centre"].id, sample_centre_and_test["test"].id)

    idemp_key = "client_idem_998877"
    res1 = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": booking["amount"],
        "idempotency_key": idemp_key,
        "simulate_status": "SUCCESS"
    })
    assert res1.status_code == status.HTTP_200_OK
    txn_id = res1.json()["transaction_id"]

    # Re-sending with the exact same idempotency key
    res2 = client.post("/api/v1/payments/", headers=headers, json={
        "booking_id": booking["id"],
        "amount": booking["amount"],
        "idempotency_key": idemp_key,
        "simulate_status": "SUCCESS"
    })
    assert res2.status_code == status.HTTP_200_OK
    assert res2.json()["transaction_id"] == txn_id
    assert "Idempotent payment request" in res2.json()["message"]
