from fastapi import status


def test_user_signup_success(client):
    payload = {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "full_name": "Rohan Patel",
        "phone": "+919876543211",
        "role": "PATIENT"
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "Rohan Patel"
    assert "hashed_password" not in data
    assert data["role"] == "PATIENT"


def test_user_signup_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "User One"
    }
    res1 = client.post("/api/v1/auth/signup", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/api/v1/auth/signup", json=payload)
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res2.json()["detail"]


def test_user_signup_validation_errors(client):
    # Short password
    res = client.post("/api/v1/auth/signup", json={
        "email": "badpass@example.com",
        "password": "123",
        "full_name": "Bad Pass"
    })
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid email
    res2 = client.post("/api/v1/auth/signup", json={
        "email": "not-an-email",
        "password": "validPassword123!",
        "full_name": "Bad Email"
    })
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_user_login_success_and_jwt(client):
    signup_data = {
        "email": "loginuser@example.com",
        "password": "MySecretPassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/signup", json=signup_data)

    login_res = client.post("/api/v1/auth/login", json={
        "email": "loginuser@example.com",
        "password": "MySecretPassword123"
    })
    assert login_res.status_code == status.HTTP_200_OK
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@example.com"


def test_user_login_invalid_password(client):
    signup_data = {
        "email": "loginfail@example.com",
        "password": "CorrectPassword123",
        "full_name": "Login Fail"
    }
    client.post("/api/v1/auth/signup", json=signup_data)

    login_res = client.post("/api/v1/auth/login", json={
        "email": "loginfail@example.com",
        "password": "WrongPassword456"
    })
    assert login_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in login_res.json()["detail"]


def test_get_current_user_profile(client, test_users):
    headers = test_users["patient1_headers"]
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "patient1@eve.com"


def test_get_profile_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
