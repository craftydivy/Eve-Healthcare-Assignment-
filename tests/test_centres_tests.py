from fastapi import status


def test_list_diagnostic_tests(client, sample_centre_and_test):
    response = client.get("/api/v1/tests/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    assert any(item["code"] == "CBT-01" for item in data["items"])


def test_create_test_admin_only(client, test_users):
    # As patient (should be forbidden)
    patient_headers = test_users["patient1_headers"]
    res_patient = client.post(
        "/api/v1/tests/",
        headers=patient_headers,
        json={
            "name": "Unauthorized Test",
            "code": "UNAUTH-01",
            "category": "Pathology",
        }
    )
    assert res_patient.status_code == status.HTTP_403_FORBIDDEN

    # As Admin (should succeed)
    admin_headers = test_users["admin_headers"]
    res_admin = client.post(
        "/api/v1/tests/",
        headers=admin_headers,
        json={
            "name": "Advanced Renal Panel",
            "code": "RENAL-01",
            "category": "Biochemistry",
            "sample_type": "Blood & Urine",
            "preparation_instructions": "Hydrate normally",
        }
    )
    assert res_admin.status_code == status.HTTP_201_CREATED
    data = res_admin.json()
    assert data["code"] == "RENAL-01"
    assert data["name"] == "Advanced Renal Panel"


def test_list_centres_and_filtering(client, sample_centre_and_test):
    response = client.get("/api/v1/centres/?city=Mumbai")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["city"] == "Mumbai"


def test_get_centre_with_tests_and_prices(client, sample_centre_and_test):
    centre_id = sample_centre_and_test["centre"].id
    response = client.get(f"/api/v1/centres/{centre_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Metropolis Lab"
    assert len(data["centre_tests"]) >= 1
    test_offering = data["centre_tests"][0]
    assert float(test_offering["price"]) == 500.00
    assert test_offering["turnaround_hours"] == 24


def test_update_test_price_at_centre(client, test_users, sample_centre_and_test):
    centre_id = sample_centre_and_test["centre"].id
    test_id = sample_centre_and_test["test"].id
    admin_headers = test_users["admin_headers"]

    res = client.put(
        f"/api/v1/centres/{centre_id}/tests/{test_id}",
        headers=admin_headers,
        json={"price": 650.00, "turnaround_hours": 18}
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert float(data["price"]) == 650.00
    assert data["turnaround_hours"] == 18
