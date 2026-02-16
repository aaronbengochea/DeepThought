"""Integration tests for the full API flow through HTTP.

Tests the complete request/response pipeline including middleware,
serialization, JWT auth headers, and dependency injection overrides.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from deepthought.api.app import create_app
from deepthought.api.auth import create_access_token, hash_password
from deepthought.api.dependencies import (
    get_agent_graph,
    get_logs_db_client,
    get_pairs_db_client,
    get_users_db_client,
)


@pytest.fixture
def mock_users_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=None)
    mock.put_item = AsyncMock(return_value=None)
    mock.query = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_pairs_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=None)
    mock.put_item = AsyncMock(return_value=None)
    mock.query = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_logs_db():
    mock = MagicMock()
    mock.get_item = AsyncMock(return_value=None)
    mock.put_item = AsyncMock(return_value=None)
    mock.query = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_graph():
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value={
        "plan": None,
        "execution_result": None,
        "verification_result": None,
        "formatted_response": None,
        "node_timings": {},
    })
    return mock


@pytest.fixture
def app(mock_users_db, mock_pairs_db, mock_logs_db, mock_graph):
    application = create_app()
    application.dependency_overrides[get_users_db_client] = lambda: mock_users_db
    application.dependency_overrides[get_pairs_db_client] = lambda: mock_pairs_db
    application.dependency_overrides[get_logs_db_client] = lambda: mock_logs_db
    application.dependency_overrides[get_agent_graph] = lambda: mock_graph
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def make_auth_header(email: str = "test@example.com") -> dict[str, str]:
    """Create a Bearer token header for the given email."""
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Auth flow
# ---------------------------------------------------------------------------


class TestSignupFlow:
    """Tests for POST /api/v1/auth/signup."""

    def test_signup_success(self, client, mock_users_db):
        mock_users_db.get_item = AsyncMock(return_value=None)

        resp = client.post("/api/v1/auth/signup", json={
            "email": "new@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "secure123",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert "token" in body
        assert body["user"]["email"] == "new@example.com"
        assert body["user"]["first_name"] == "Jane"
        assert body["user"]["last_name"] == "Doe"
        assert "created_at" in body["user"]
        mock_users_db.put_item.assert_called_once()

    def test_signup_duplicate_email_returns_409(self, client, mock_users_db):
        mock_users_db.get_item = AsyncMock(return_value={"pk": "existing@example.com"})

        resp = client.post("/api/v1/auth/signup", json={
            "email": "existing@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "secure123",
        })

        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_signup_missing_fields_returns_422(self, client):
        resp = client.post("/api/v1/auth/signup", json={"email": "bad@example.com"})
        assert resp.status_code == 422


class TestSigninFlow:
    """Tests for POST /api/v1/auth/signin."""

    def test_signin_success(self, client, mock_users_db):
        hashed = hash_password("correctpassword")
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": hashed,
        })

        resp = client.post("/api/v1/auth/signin", json={
            "email": "user@example.com",
            "password": "correctpassword",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert "token" in body
        assert body["email"] == "user@example.com"

    def test_signin_wrong_password_returns_401(self, client, mock_users_db):
        hashed = hash_password("correctpassword")
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "password_hash": hashed,
        })

        resp = client.post("/api/v1/auth/signin", json={
            "email": "user@example.com",
            "password": "wrongpassword",
        })

        assert resp.status_code == 401

    def test_signin_nonexistent_user_returns_401(self, client, mock_users_db):
        mock_users_db.get_item = AsyncMock(return_value=None)

        resp = client.post("/api/v1/auth/signin", json={
            "email": "nobody@example.com",
            "password": "anything",
        })

        assert resp.status_code == 401


class TestProfileFlow:
    """Tests for GET /api/v1/auth/profile."""

    def test_profile_with_valid_token(self, client, mock_users_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "created_at": "2025-01-01T00:00:00+00:00",
        })

        resp = client.get("/api/v1/auth/profile", headers=make_auth_header("user@example.com"))

        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "user@example.com"
        assert body["first_name"] == "Test"
        assert body["last_name"] == "User"

    def test_profile_without_token_returns_401(self, client):
        resp = client.get("/api/v1/auth/profile")
        assert resp.status_code == 401

    def test_profile_with_invalid_token_returns_401(self, client):
        resp = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Pairs flow
# ---------------------------------------------------------------------------


class TestCreatePairFlow:
    """Tests for POST /api/v1/pairs."""

    def test_create_pair_success(self, client, mock_users_db, mock_pairs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })

        resp = client.post(
            "/api/v1/pairs",
            json={"val1": 42, "val2": 58},
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["val1"] == 42
        assert body["val2"] == 58
        assert "pair_id" in body
        assert "created_at" in body
        mock_pairs_db.put_item.assert_called_once()

    def test_create_pair_without_auth_returns_401(self, client):
        resp = client.post("/api/v1/pairs", json={"val1": 1, "val2": 2})
        assert resp.status_code == 401

    def test_create_pair_with_floats(self, client, mock_users_db, mock_pairs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })

        resp = client.post(
            "/api/v1/pairs",
            json={"val1": 3.14, "val2": 2.71},
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 201
        assert resp.json()["val1"] == 3.14


class TestListPairsFlow:
    """Tests for GET /api/v1/pairs."""

    def test_list_pairs_empty(self, client, mock_users_db, mock_pairs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.query = AsyncMock(return_value=[])

        resp = client.get(
            "/api/v1/pairs",
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_pairs_returns_user_pairs(self, client, mock_users_db, mock_pairs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.query = AsyncMock(return_value=[
            {"sk": "pair-1", "val1": 10, "val2": 20, "created_at": "2025-01-01T00:00:00+00:00"},
            {"sk": "pair-2", "val1": 30, "val2": 40, "created_at": "2025-01-01T00:00:00+00:00"},
        ])

        resp = client.get(
            "/api/v1/pairs",
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["pair_id"] == "pair-1"
        assert body[1]["pair_id"] == "pair-2"

    def test_list_pairs_without_auth_returns_401(self, client):
        resp = client.get("/api/v1/pairs")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Operations flow
# ---------------------------------------------------------------------------


class TestOperateFlow:
    """Tests for POST /api/v1/pairs/{pair_id}/operate."""

    def test_operate_pair_not_found_returns_404(self, client, mock_users_db, mock_pairs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.get_item = AsyncMock(return_value=None)

        resp = client.post(
            "/api/v1/pairs/nonexistent/operate",
            json={"operation": "add"},
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 404

    def test_operate_success(self, client, mock_users_db, mock_pairs_db, mock_logs_db, mock_graph):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 5,
        })

        mock_exec = MagicMock()
        mock_exec.final_value = 15
        mock_exec.success = True
        mock_exec.model_dump = MagicMock(return_value={"final_value": 15, "success": True})

        mock_graph.ainvoke = AsyncMock(return_value={
            "plan": None,
            "execution_result": mock_exec,
            "verification_result": None,
            "formatted_response": None,
            "node_timings": {"execution": 5.0},
        })

        resp = client.post(
            "/api/v1/pairs/pair-123/operate",
            json={"operation": "add"},
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["pair_id"] == "pair-123"
        assert body["operation"] == "add"
        assert body["result"] == 15
        assert body["success"] is True
        assert "agent_steps" in body
        mock_logs_db.put_item.assert_called_once()

    def test_operate_without_auth_returns_401(self, client):
        resp = client.post(
            "/api/v1/pairs/pair-123/operate",
            json={"operation": "add"},
        )
        assert resp.status_code == 401

    def test_operate_graph_failure_returns_500(
        self, client, mock_users_db, mock_pairs_db, mock_graph
    ):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 0,
        })
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        resp = client.post(
            "/api/v1/pairs/pair-123/operate",
            json={"operation": "divide"},
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 500


class TestGetLogsFlow:
    """Tests for GET /api/v1/pairs/{pair_id}/logs."""

    def test_get_logs_pair_not_found_returns_404(self, client, mock_users_db, mock_pairs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.get_item = AsyncMock(return_value=None)

        resp = client.get(
            "/api/v1/pairs/nonexistent/logs",
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 404

    def test_get_logs_returns_entries(self, client, mock_users_db, mock_pairs_db, mock_logs_db):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "sk": "pair-123",
            "val1": 10,
            "val2": 20,
        })
        mock_logs_db.query = AsyncMock(return_value=[
            {
                "log_id": "log-1",
                "pair_id": "pair-123",
                "operation": "add",
                "agent_steps": [],
                "result": 30,
                "success": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            },
        ])

        resp = client.get(
            "/api/v1/pairs/pair-123/logs",
            headers=make_auth_header("user@example.com"),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["log_id"] == "log-1"
        assert body[0]["result"] == 30

    def test_get_logs_without_auth_returns_401(self, client):
        resp = client.get("/api/v1/pairs/pair-123/logs")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Cross-user ownership isolation
# ---------------------------------------------------------------------------


class TestOwnershipIsolation:
    """Tests that users cannot access another user's pairs."""

    def test_operate_on_other_users_pair_returns_404(
        self, client, mock_users_db, mock_pairs_db
    ):
        """User A's token should not access User B's pair (get_item returns None for wrong pk)."""
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "userA@example.com",
            "first_name": "User",
            "last_name": "A",
        })
        # Pair lookup with pk=userA returns None (pair belongs to userB)
        mock_pairs_db.get_item = AsyncMock(return_value=None)

        resp = client.post(
            "/api/v1/pairs/userB-pair-id/operate",
            json={"operation": "add"},
            headers=make_auth_header("userA@example.com"),
        )

        assert resp.status_code == 404

    def test_get_logs_of_other_users_pair_returns_404(
        self, client, mock_users_db, mock_pairs_db
    ):
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "userA@example.com",
            "first_name": "User",
            "last_name": "A",
        })
        mock_pairs_db.get_item = AsyncMock(return_value=None)

        resp = client.get(
            "/api/v1/pairs/userB-pair-id/logs",
            headers=make_auth_header("userA@example.com"),
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Full signup → create pair → operate → view logs flow
# ---------------------------------------------------------------------------


class TestEndToEndFlow:
    """Tests the full user journey through the API."""

    def test_signup_create_pair_operate_view_logs(
        self, client, mock_users_db, mock_pairs_db, mock_logs_db, mock_graph
    ):
        # 1. Sign up
        mock_users_db.get_item = AsyncMock(return_value=None)
        signup_resp = client.post("/api/v1/auth/signup", json={
            "email": "e2e@example.com",
            "first_name": "End",
            "last_name": "ToEnd",
            "password": "testpass123",
        })
        assert signup_resp.status_code == 201
        token = signup_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # From now on, the user exists
        mock_users_db.get_item = AsyncMock(return_value={
            "pk": "e2e@example.com",
            "first_name": "End",
            "last_name": "ToEnd",
            "created_at": "2025-01-01T00:00:00+00:00",
        })

        # 2. Create a pair
        pair_resp = client.post("/api/v1/pairs", json={"val1": 100, "val2": 200}, headers=headers)
        assert pair_resp.status_code == 201
        pair_id = pair_resp.json()["pair_id"]

        # 3. Operate on the pair
        mock_pairs_db.get_item = AsyncMock(return_value={
            "pk": "e2e@example.com",
            "sk": pair_id,
            "val1": 100,
            "val2": 200,
        })

        mock_exec = MagicMock()
        mock_exec.final_value = 300
        mock_exec.success = True
        mock_exec.model_dump = MagicMock(return_value={"final_value": 300, "success": True})

        mock_graph.ainvoke = AsyncMock(return_value={
            "plan": None,
            "execution_result": mock_exec,
            "verification_result": None,
            "formatted_response": None,
            "node_timings": {"execution": 3.0},
        })

        operate_resp = client.post(
            f"/api/v1/pairs/{pair_id}/operate",
            json={"operation": "add"},
            headers=headers,
        )
        assert operate_resp.status_code == 200
        assert operate_resp.json()["result"] == 300
        assert operate_resp.json()["success"] is True

        # 4. View logs
        log_entry = operate_resp.json()
        mock_logs_db.query = AsyncMock(return_value=[
            {
                "log_id": log_entry["log_id"],
                "pair_id": pair_id,
                "operation": "add",
                "agent_steps": log_entry["agent_steps"],
                "result": 300,
                "success": True,
                "created_at": log_entry["created_at"],
            },
        ])

        logs_resp = client.get(f"/api/v1/pairs/{pair_id}/logs", headers=headers)
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        assert len(logs) == 1
        assert logs[0]["operation"] == "add"
        assert logs[0]["result"] == 300
