"""API integration tests - auth flow, query endpoint, citation -> Markdown evidence.

Uses the real `policylens_test` database (via a FastAPI dependency override) and the
real demo credentials from .env, so this exercises the actual request path end to end.
"""

import pytest
from fastapi.testclient import TestClient

from app.auth.service import hash_password
from app.config import get_settings

TEST_USERNAME = "test-demo-user"
TEST_PASSWORD = "test-password-123"


@pytest.fixture
def client(engine):
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            yield session

    # Independent of whatever DEMO_USERNAME/DEMO_PASSWORD_HASH happen to be in .env,
    # so this test is reproducible in CI regardless of local dev secrets.
    test_settings = get_settings().model_copy(
        update={"demo_username": TEST_USERNAME, "demo_password_hash": hash_password(TEST_PASSWORD)}
    )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def demo_credentials():
    return TEST_USERNAME


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200


def test_readyz_checks_db(client):
    response = client.get("/readyz")
    assert response.status_code == 200


def test_query_requires_auth(client):
    response = client.post("/api/v1/query", json={"question": "anything"})
    assert response.status_code == 401


def test_login_wrong_password_rejected(client, demo_credentials):
    response = client.post(
        "/auth/login", json={"username": demo_credentials, "password": "definitely-wrong"}
    )
    assert response.status_code == 401


def test_login_then_logout(client, demo_credentials):
    login = client.post(
        "/auth/login", json={"username": demo_credentials, "password": TEST_PASSWORD}
    )
    assert login.status_code == 200, login.text
    assert "policylens_session" in login.cookies

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == demo_credentials

    logout = client.post("/auth/logout")
    assert logout.status_code == 200

    after_logout = client.post("/api/v1/query", json={"question": "anything"})
    assert after_logout.status_code == 401


@pytest.mark.skipif(not get_settings().openai_api_key, reason="OPENAI_API_KEY not configured")
def test_login_then_query_then_trace(client, demo_credentials):
    client.post("/auth/login", json={"username": demo_credentials, "password": TEST_PASSWORD})

    query = client.post(
        "/api/v1/query", json={"question": "What is the management fee for ISIN LU1234567896?"}
    )
    assert query.status_code == 200
    body = query.json()
    assert "1.20" in body["answer"]
    assert body["citations"]
    request_id = body["request_id"]

    trace = client.get(f"/api/v1/requests/{request_id}/trace")
    assert trace.status_code == 200
    assert trace.json()["tool_calls"]


@pytest.mark.skipif(not get_settings().openai_api_key, reason="OPENAI_API_KEY not configured")
def test_citation_links_to_servable_markdown(client, demo_credentials):
    client.post("/auth/login", json={"username": demo_credentials, "password": TEST_PASSWORD})
    query = client.post(
        "/api/v1/query", json={"question": "What is the management fee for ISIN LU1234567896?"}
    )
    citation = query.json()["citations"][0]

    markdown = client.get(f"/api/v1/documents/{citation['filename']}/markdown")
    assert markdown.status_code == 200
    assert "LU1234567896" in markdown.text


def test_markdown_requires_auth(client):
    response = client.get("/api/v1/documents/anything.pdf/markdown")
    assert response.status_code == 401


def test_markdown_404_for_unknown_document(client, demo_credentials):
    client.post("/auth/login", json={"username": demo_credentials, "password": TEST_PASSWORD})
    response = client.get("/api/v1/documents/does-not-exist.pdf/markdown")
    assert response.status_code == 404
