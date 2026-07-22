"""
Integration tests for authentication and route-level auth guards.

These hit the real FastAPI app + a real Postgres connection (via
`get_db`/`init_db`), so the `database` container from docker-compose.yml
must be running. Each test registers a fresh, uuid-suffixed username to
avoid colliding with data left behind by previous runs.
"""
import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from backend.main import app

load_dotenv()

client = TestClient(app)


def _unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _register(username: str, password: str = "pw123456", admin_code: str = None) -> dict:
    payload = {"username": username, "password": password, "name": "Test Teacher"}
    if admin_code is not None:
        payload["admin_code"] = admin_code
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _login(username: str, password: str = "pw123456") -> str:
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_register_and_login_success():
    username = _unique_username("teacher")
    _register(username)
    token = _login(username)
    assert token


def test_login_wrong_password():
    username = _unique_username("teacher")
    _register(username)
    response = client.post("/auth/token", data={"username": username, "password": "wrong-password"})
    assert response.status_code == 401


def test_lessons_requires_auth():
    response = client.get("/lessons/")
    assert response.status_code == 401


def test_lessons_with_valid_token():
    username = _unique_username("teacher")
    _register(username)
    token = _login(username)
    response = client.get("/lessons/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_admin_registration_grants_analytics_access():
    admin_code = os.getenv("ADMIN_SIGNUP_CODE")
    if not admin_code:
        pytest.skip("ADMIN_SIGNUP_CODE not configured in this environment.")

    username = _unique_username("admin")
    data = _register(username, admin_code=admin_code)
    assert data["role"] == "admin"

    token = _login(username)
    response = client.get("/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_analytics_forbidden_for_teacher_role():
    username = _unique_username("teacher")
    _register(username)
    token = _login(username)
    response = client.get("/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_generate_lesson_502_on_gemini_failure():
    """Regression test: /generate_lesson must surface a clean 502, not a
    None/malformed 200, when Gemini exhausts retries without usable output."""
    username = _unique_username("teacher")
    _register(username)
    token = _login(username)

    with patch("backend.routes.lesson.generator.generate_lesson", new=AsyncMock(return_value=None)):
        response = client.post(
            "/generate_lesson",
            json={"subject": "Math", "topic": "Fractions", "level": "JSS2"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 502
