from datetime import datetime, timezone, timedelta
from fastapi import status


def test_create_booking_success(client, test_users, sample_centre_and_test):
    patient_headers = test_users["patient1_headers"]
    centre = sample_centre_and_test["centre"]
    test = sample_centre_and_test["test"]

    # Valid future appointment time (tomorrow at 10:00 AM)
    future_time = datetime.now(timezone.utc) + timedelta(days=1)
    future_time = future_time.replace(hour=10, minute=0, second=0, microsecond=0)

    booking_payload = {
        "centre_id": centre.id,
        "test_id": test.id,
        "appointment_time": future_time.isoformat(),
        "patient_name": "John Doe",
        "patient_age": 32,
        "patient_gender": "Male",
        "patient_phone": "+919876543210",
        "notes": "First time visit"
    }

    response = client.post("/api/v1/bookings/", headers=patient_headers, json=booking_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["booking_ref"].startswith("EVE-")
    assert data["status"] == "PENDING"
    assert float(data["amount"]) == 500.00  # Price frozen from centre_test
    assert data["patient_name"] == "John Doe"


def test_booking_past_date_validation_error(client, test_users, sample_centre_and_test):
    patient_headers = test_users["patient1_headers"]
    centre = sample_centre_and_test["centre"]
    test = sample_centre_and_test["test"]

    # Past time (yesterday)
    past_time = datetime.now(timezone.utc) - timedelta(days=1)

    booking_payload = {
        "centre_id": centre.id,
        "test_id": test.id,
        "appointment_time": past_time.isoformat(),
        "patient_name": "Invalid Date",
        "patient_age": 25,
    }

    response = client.post("/api/v1/bookings/", headers=patient_headers, json=booking_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Appointment time must be in the future" in response.text


def test_booking_test_not_offered_at_centre(client, test_users, sample_centre_and_test):
    patient_headers = test_users["patient1_headers"]
    centre = sample_centre_and_test["centre"]

    future_time = datetime.now(timezone.utc) + timedelta(days=2)

    booking_payload = {
        "centre_id": centre.id,
        "test_id": 99999,  # Non-existent test
        "appointment_time": future_time.isoformat(),
        "patient_name": "Test",
    }

    response = client.post("/api/v1/bookings/", headers=patient_headers, json=booking_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_booking_authorization_user_isolation(client, test_users, sample_centre_and_test):
    # Patient 1 creates a booking
    patient1_headers = test_users["patient1_headers"]
    patient2_headers = test_users["patient2_headers"]
    centre = sample_centre_and_test["centre"]
    test = sample_centre_and_test["test"]

    future_time = datetime.now(timezone.utc) + timedelta(days=1, hours=2)

    res = client.post("/api/v1/bookings/", headers=patient1_headers, json={
        "centre_id": centre.id,
        "test_id": test.id,
        "appointment_time": future_time.isoformat(),
        "patient_name": "Patient 1",
    })
    booking_id = res.json()["id"]

    # Patient 2 attempts to view Patient 1's booking -> 403 Forbidden!
    res_unauth = client.get(f"/api/v1/bookings/{booking_id}", headers=patient2_headers)
    assert res_unauth.status_code == status.HTTP_403_FORBIDDEN

    # Patient 1 views their own booking -> 200 OK
    res_auth = client.get(f"/api/v1/bookings/{booking_id}", headers=patient1_headers)
    assert res_auth.status_code == status.HTTP_200_OK


def test_cancel_booking_workflow(client, test_users, sample_centre_and_test):
    patient1_headers = test_users["patient1_headers"]
    centre = sample_centre_and_test["centre"]
    test = sample_centre_and_test["test"]

    future_time = datetime.now(timezone.utc) + timedelta(days=1, hours=4)
    res = client.post("/api/v1/bookings/", headers=patient1_headers, json={
        "centre_id": centre.id,
        "test_id": test.id,
        "appointment_time": future_time.isoformat(),
        "patient_name": "Cancel Me",
    })
    booking_id = res.json()["id"]

    # Cancel booking
    cancel_res = client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=patient1_headers)
    assert cancel_res.status_code == status.HTTP_200_OK
    assert cancel_res.json()["status"] == "CANCELLED"

    # Attempt to cancel again -> 400 Bad Request
    re_cancel_res = client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=patient1_headers)
    assert re_cancel_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been cancelled" in re_cancel_res.json()["detail"]
