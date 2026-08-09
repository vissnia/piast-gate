import pytest
from fastapi.testclient import TestClient
from api.main import create_app
from api.config.config import settings


@pytest.fixture
def restore_cors_settings():
    original = (
        settings.cors_origins,
        settings.allow_credentials,
        settings.cors_methods,
        settings.cors_headers,
    )
    yield
    (
        settings.cors_origins,
        settings.allow_credentials,
        settings.cors_methods,
        settings.cors_headers,
    ) = original


def _build_client(cors_origins, allow_credentials=False):
    """Builds a fresh app/client since CORSMiddleware bakes in settings at construction time."""
    settings.cors_origins = cors_origins
    settings.allow_credentials = allow_credentials
    return TestClient(create_app())


def test_preflight_allowed_origin_gets_cors_headers(restore_cors_settings):
    client = _build_client(["https://allowed.example.com"])

    response = client.options(
        "/v1/api/anonymize/text",
        headers={
            "Origin": "https://allowed.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://allowed.example.com"


def test_preflight_disallowed_origin_has_no_cors_headers(restore_cors_settings):
    client = _build_client(["https://allowed.example.com"])

    response = client.options(
        "/v1/api/anonymize/text",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_actual_request_allowed_origin_echoes_header(restore_cors_settings):
    client = _build_client(["https://allowed.example.com"])

    response = client.get("/health", headers={"Origin": "https://allowed.example.com"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://allowed.example.com"


def test_actual_request_disallowed_origin_has_no_cors_header(restore_cors_settings):
    client = _build_client(["https://allowed.example.com"])

    response = client.get("/health", headers={"Origin": "https://evil.example.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_no_configured_origins_never_grants_cors_access(restore_cors_settings):
    client = _build_client([])

    response = client.get("/health", headers={"Origin": "https://anything.example.com"})

    assert "access-control-allow-origin" not in response.headers


def test_credentials_header_present_when_allow_credentials_true(restore_cors_settings):
    client = _build_client(["https://allowed.example.com"], allow_credentials=True)

    response = client.get("/health", headers={"Origin": "https://allowed.example.com"})

    assert response.headers.get("access-control-allow-credentials") == "true"


def test_credentials_header_absent_when_allow_credentials_false(restore_cors_settings):
    client = _build_client(["https://allowed.example.com"], allow_credentials=False)

    response = client.get("/health", headers={"Origin": "https://allowed.example.com"})

    assert "access-control-allow-credentials" not in response.headers


def test_wildcard_origin_allows_any_origin(restore_cors_settings):
    client = _build_client(["*"], allow_credentials=False)

    response = client.get("/health", headers={"Origin": "https://anything.example.com"})

    assert response.headers.get("access-control-allow-origin") == "*"


def test_wildcard_origin_with_credentialed_request_reflects_exact_origin(restore_cors_settings):
    """A cookie-bearing request under wildcard+credentials must get the exact origin back, not '*'."""
    client = _build_client(["*"], allow_credentials=True)

    response = client.get(
        "/health",
        headers={"Origin": "https://anything.example.com", "Cookie": "session=abc"},
    )

    assert response.headers.get("access-control-allow-origin") == "https://anything.example.com"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_wildcard_preflight_with_credentials_reflects_exact_origin(restore_cors_settings):
    client = _build_client(["*"], allow_credentials=True)

    response = client.options(
        "/v1/api/anonymize/text",
        headers={
            "Origin": "https://anything.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.headers.get("access-control-allow-origin") == "https://anything.example.com"
    assert response.headers.get("access-control-allow-credentials") == "true"
