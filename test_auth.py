import asyncio
import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app

# Ensure test JWT secret for reproducibility
os.environ.setdefault("JWT_SECRET_KEY", "test_secret")

@pytest.mark.asyncio
async def test_signup_and_login(monkeypatch):
    # Use an in-memory like database? We'll assume real Mongo with MONGO_URI set.
    # If MONGO_URI not set, skip.
    if not os.getenv("MONGO_URI"):
        pytest.skip("MONGO_URI not set; integration test skipped")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        signup_payload = {"name": "Test User", "email": "test_user@example.com", "password": "Password123!"}
        r = await ac.post("/auth/signup", json=signup_payload)
        # Allow 400 if user exists from prior run
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST)

        login_payload = {"email": signup_payload["email"], "password": signup_payload["password"]}
        r2 = await ac.post("/auth/login", json=login_payload)
        assert r2.status_code == status.HTTP_200_OK
        token = r2.json()["access_token"]
        assert token

        r3 = await ac.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == status.HTTP_200_OK
        data = r3.json()
        assert data["email"] == signup_payload["email"]
