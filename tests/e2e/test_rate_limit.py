import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address


@pytest.fixture
def low_rate_limit(app):
    """
    Temporarily swaps app.state.limiter for one with a much lower limit and its
    own isolated in-memory storage, so this test never touches (or is affected
    by) the request budget shared with other test modules.
    """
    original_limiter = app.state.limiter
    app.state.limiter = Limiter(key_func=get_remote_address, default_limits=["2/minute"])
    yield
    app.state.limiter = original_limiter


def test_requests_within_limit_succeed(client, auth_headers, low_rate_limit):
    for _ in range(2):
        response = client.post(
            "/v1/api/anonymize/text", json={"text": "hello"}, headers=auth_headers
        )
        assert response.status_code == 200


def test_request_over_limit_is_rejected_with_429(client, auth_headers, low_rate_limit):
    for _ in range(2):
        response = client.post(
            "/v1/api/anonymize/text", json={"text": "hello"}, headers=auth_headers
        )
        assert response.status_code == 200

    response = client.post(
        "/v1/api/anonymize/text", json={"text": "hello"}, headers=auth_headers
    )

    assert response.status_code == 429
    body = response.json()
    assert "Rate limit exceeded" in body["error"]


def test_limit_bucket_is_isolated_per_route(client, auth_headers, low_rate_limit):
    """
    slowapi's default key_style="url" scopes each bucket to (client IP, path), so
    exhausting the limit on one route must not affect a different route.
    """
    for _ in range(2):
        response = client.post(
            "/v1/api/anonymize/text", json={"text": "a"}, headers=auth_headers
        )
        assert response.status_code == 200

    exhausted = client.post(
        "/v1/api/anonymize/text", json={"text": "b"}, headers=auth_headers
    )
    assert exhausted.status_code == 429

    other_route = client.get("/v1/api/tags")
    assert other_route.status_code == 200


def test_unauthorized_requests_still_consume_the_limit(client, low_rate_limit):
    """The rate limiter runs before the auth dependency, so failed auth still counts."""
    for _ in range(2):
        response = client.post("/v1/api/anonymize/text", json={"text": "x"})
        assert response.status_code == 401

    response = client.post("/v1/api/anonymize/text", json={"text": "x"})
    assert response.status_code == 429
