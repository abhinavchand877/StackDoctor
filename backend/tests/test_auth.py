import json

def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "username": "newdev",
        "email": "newdev@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "access_token" in data
    assert data["user"]["username"] == "newdev"
    assert data["user"]["email"] == "newdev@example.com"

def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={
        "username": "dupedev",
        "email": "dupe1@example.com",
        "password": "Password123!"
    })
    res = client.post("/api/auth/register", json={
        "username": "dupedev",
        "email": "dupe2@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 409
    assert "already registered" in res.get_json()["message"]

def test_register_invalid_email(client):
    res = client.post("/api/auth/register", json={
        "username": "invaliduser",
        "email": "not-an-email",
        "password": "Password123!"
    })
    assert res.status_code == 400
    assert "valid email" in res.get_json()["message"]

def test_login_success(client, test_user):
    res = client.post("/api/auth/login", json={
        "identifier": "testdev@example.com",
        "password": "SecurePass123!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert data["user"]["username"] == "testdev"

def test_login_invalid_password(client, test_user):
    res = client.post("/api/auth/login", json={
        "identifier": "testdev@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.get_json()["message"]

def test_me_endpoint_authenticated(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["user"]["username"] == "testdev"

def test_me_endpoint_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
