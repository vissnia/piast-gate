from api.config.config import settings


def test_oversized_body_rejected_before_reaching_the_endpoint(client, auth_headers):
    """
    Unlike the document-upload size check, this must reject any endpoint —
    including plain JSON ones that have no upload-size guard of their own.
    """
    old_size = settings.max_upload_size
    settings.max_upload_size = 1024
    try:
        response = client.post(
            "/v1/api/anonymize/text",
            json={"text": "a" * 200_000},
            headers=auth_headers,
        )

        assert response.status_code == 413
        assert "Request body too large" in response.json()["error"]["message"]
    finally:
        settings.max_upload_size = old_size


def test_body_within_limit_is_not_rejected(client, auth_headers):
    old_size = settings.max_upload_size
    settings.max_upload_size = 1024
    try:
        response = client.post(
            "/v1/api/anonymize/text", json={"text": "hello"}, headers=auth_headers
        )
        assert response.status_code == 200
    finally:
        settings.max_upload_size = old_size


def test_request_without_content_length_passes_through(client):
    """GET requests carry no body/Content-Length and must not be affected."""
    response = client.get("/v1/api/tags")
    assert response.status_code == 200
