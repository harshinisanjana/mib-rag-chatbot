import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserRole

client = TestClient(app)


def test_admin_login_success():
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@example.com"
    assert data["user"]["role"] == "admin"


def test_agent_login_success():
    response = client.post(
        "/api/auth/login",
        json={"email": "agent@example.com", "password": "Agent123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "agent@example.com"
    assert data["user"]["role"] == "support_agent"


def test_login_invalid_password():
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_user():
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "SomePassword!"}
    )
    assert response.status_code == 401


def test_get_me_authenticated():
    # Login as admin
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"}
    )
    token = login_res.json()["access_token"]

    # Call /me
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "admin@example.com"
    assert me_data["role"] == "admin"


def test_get_me_unauthenticated():
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 401


def test_role_authorization_admin_only():
    # Login as support agent
    agent_login = client.post(
        "/api/auth/login",
        json={"email": "agent@example.com", "password": "Agent123!"}
    )
    agent_token = agent_login.json()["access_token"]

    # Try creating user as agent (should be 403 Forbidden)
    create_res = client.post(
        "/api/auth/users",
        json={
            "name": "New Agent",
            "email": "newagent@example.com",
            "password": "Password123!",
            "role": "support_agent"
        },
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    assert create_res.status_code == 403

    # Login as admin
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"}
    )
    admin_token = admin_login.json()["access_token"]

    # Try creating user as admin (should succeed or return 400 if already exists)
    import time
    unique_email = f"agent_{int(time.time())}@example.com"
    create_res_admin = client.post(
        "/api/auth/users",
        json={
            "name": "New Admin Created Agent",
            "email": unique_email,
            "password": "Password123!",
            "role": "support_agent"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res_admin.status_code == 201
    assert create_res_admin.json()["email"] == unique_email
