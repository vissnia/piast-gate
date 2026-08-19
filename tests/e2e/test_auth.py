import pytest
from api.config.config import settings
from api.config.auth import verify_api_key
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture
def restore_api_keys():
    original = settings.api_keys
    yield
    settings.api_keys = original


def test_missing_authorization_header(client):
    response = client.post("/v1/api/anonymize/text", json={"text": "hello"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing Authorization Token"
    assert response.headers.get("www-authenticate") == "Bearer"


def test_invalid_token(client):
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_empty_bearer_token(client):
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": "Bearer "},
    )
    assert response.status_code == 401


def test_non_bearer_auth_scheme_rejected(client):
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": "Basic dGVzdC1hcGkta2V5"},
    )
    assert response.status_code == 401


def test_malformed_header_without_scheme_rejected(client, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": token},
    )
    assert response.status_code == 401


def test_bearer_scheme_is_case_insensitive(client, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": f"bearer {token}"},
    )
    assert response.status_code == 200


def test_token_with_trailing_whitespace_is_rejected(client, auth_headers):
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": auth_headers["Authorization"] + " "},
    )
    assert response.status_code == 401


def test_token_is_case_sensitive(client):
    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": "Bearer TEST-API-KEY"},
    )
    assert response.status_code == 401


def test_multiple_configured_keys_each_valid(client, restore_api_keys):
    settings.api_keys = {"test-api-key": "client-one", "second-valid-key": "client-two"}

    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": "Bearer second-valid-key"},
    )
    assert response.status_code == 200


def test_key_removed_from_config_is_rejected(client, restore_api_keys):
    settings.api_keys = {"only-this-key": "client-one"}

    response = client.post(
        "/v1/api/anonymize/text",
        json={"text": "hello"},
        headers={"Authorization": "Bearer test-api-key"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_api_key_resolves_client_name(restore_api_keys):
    settings.api_keys = {"key-a": "client-a", "key-b": "client-b"}

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="key-b")
    client_name = await verify_api_key(credentials)

    assert client_name == "client-b"


def test_health_endpoint_requires_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_tags_endpoint_requires_no_auth(client):
    response = client.get("/v1/api/tags")
    assert response.status_code == 200


def test_chat_endpoint_requires_auth(client):
    response = client.post("/v1/api/chat", json={})
    assert response.status_code == 401


def test_anonymize_document_endpoint_requires_auth(client):
    response = client.post(
        "/v1/api/anonymize",
        files={"file": ("t.txt", b"x", "text/plain")},
    )
    assert response.status_code == 401
