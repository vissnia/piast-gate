import time
from io import BytesIO
import docx
from application.dtos.anonymize_request import MAX_TEXT_LENGTH
from application.dtos.chat_request import MAX_CONTENT_LENGTH, MAX_MESSAGES


def _make_docx_bytes(paragraph: str) -> bytes:
    doc = docx.Document()
    doc.add_paragraph(paragraph)
    f = BytesIO()
    doc.save(f)
    f.seek(0)
    return f.read()


def test_anonymize_text_over_max_length_rejected(client, auth_headers):
    payload = {"text": "a" * (MAX_TEXT_LENGTH + 1)}
    response = client.post("/v1/api/anonymize/text", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "text"]


def test_anonymize_text_at_max_length_accepted(client, auth_headers):
    payload = {"text": "a" * MAX_TEXT_LENGTH}
    response = client.post("/v1/api/anonymize/text", json=payload, headers=auth_headers)

    assert response.status_code == 200


def test_oversized_anonymize_text_rejected_without_expensive_processing(client, auth_headers):
    """Validation must reject before PII detection runs, so this stays fast."""
    payload = {"text": "a" * (MAX_TEXT_LENGTH * 20)}

    start = time.monotonic()
    response = client.post("/v1/api/anonymize/text", json=payload, headers=auth_headers)
    elapsed = time.monotonic() - start

    assert response.status_code == 422
    assert elapsed < 3.0


def test_chat_message_content_over_max_length_rejected(client, auth_headers):
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "a" * (MAX_CONTENT_LENGTH + 1)}],
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)

    assert response.status_code == 422


def test_chat_message_content_at_max_length_accepted(client, auth_headers):
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "a" * MAX_CONTENT_LENGTH}],
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)

    assert response.status_code == 200


def test_chat_too_many_messages_rejected(client, auth_headers):
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "hi"} for _ in range(MAX_MESSAGES + 1)],
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)

    assert response.status_code == 422


def test_chat_at_max_messages_accepted(client, auth_headers):
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "hi"} for _ in range(MAX_MESSAGES)],
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)

    assert response.status_code == 200


def test_anonymize_document_over_max_upload_size_rejected(client, auth_headers):
    from api.config.config import settings

    old_size = settings.max_upload_size
    settings.max_upload_size = 1024
    try:
        files = {"file": ("large.txt", b"A" * 2048, "text/plain")}
        response = client.post("/v1/api/anonymize", files=files, headers=auth_headers)

        assert response.status_code == 413
    finally:
        settings.max_upload_size = old_size


def test_anonymize_document_at_max_upload_size_boundary_succeeds(client, auth_headers):
    """A file whose size is exactly at the configured limit must not trip the 413 guard."""
    from api.config.config import settings

    file_bytes = _make_docx_bytes("Jan Kowalski, PESEL 90010112345.")

    old_size = settings.max_upload_size
    settings.max_upload_size = len(file_bytes)
    try:
        files = {
            "file": (
                "boundary.docx",
                file_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        response = client.post("/v1/api/anonymize", files=files, headers=auth_headers)

        assert response.status_code == 200
        assert "90010112345" not in response.json()["anonymized_text"]
    finally:
        settings.max_upload_size = old_size
