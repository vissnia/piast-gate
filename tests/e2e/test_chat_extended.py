import pytest
from api.config.config import settings


def test_chat_tool_call_passthrough(client, auth_headers):
    """Tool calls are returned untouched (not scanned for PII), with finish_reason='tool_calls'."""
    payload = {
        "messages": [{"role": "user", "content": "__TRIGGER_TOOL_CALL__"}],
        "tools": [{"type": "function", "function": {"name": "mock_tool", "parameters": {}}}],
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    message = data["choices"][0]["message"]
    assert message["content"] is None
    assert message["tool_calls"][0]["function"]["name"] == "mock_tool"
    assert data["choices"][0]["finish_reason"] == "tool_calls"


def test_chat_streaming_tool_call_passthrough(client, auth_headers):
    """Streamed tool calls arrive as a dedicated chunk after the text stream ends."""
    payload = {
        "messages": [{"role": "user", "content": "__TRIGGER_TOOL_CALL__"}],
        "tools": [{"type": "function", "function": {"name": "mock_tool", "parameters": {}}}],
        "stream": True,
    }
    with client.stream("POST", "/v1/api/chat", json=payload, headers=auth_headers) as response:
        assert response.status_code == 200
        chunks = [__import__("json").loads(line) for line in response.iter_lines() if line]

    tool_call_chunks = [c for c in chunks if c["message"].get("tool_calls")]
    assert len(tool_call_chunks) == 1
    assert tool_call_chunks[0]["message"]["tool_calls"][0]["function"]["name"] == "mock_tool"


def test_chat_multimodal_text_part_is_anonymized(client, auth_headers):
    """Only the text parts of multimodal content are anonymized/deanonymized; image parts pass through untouched."""
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Nazywam się Jan Kowalski. Mój PESEL to 90010112349."},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
                ],
            }
        ],
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    content = data["choices"][0]["message"]["content"]
    assert "90010112349" in content
    assert "Jan Kowalski" in content


def test_chat_usage_is_populated(client, auth_headers):
    """usage is real (mock-approximated word counts), not the old hardcoded zeros."""
    payload = {"messages": [{"role": "user", "content": "Cześć jak się masz"}]}
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    usage = data["usage"]
    assert usage["prompt_tokens"] > 0
    assert usage["completion_tokens"] > 0
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]


def test_chat_streaming_usage_on_final_chunk(client, auth_headers):
    """usage is None on intermediate chunks and populated only on the final done=True chunk."""
    payload = {"messages": [{"role": "user", "content": "Cześć jak się masz"}], "stream": True}
    with client.stream("POST", "/v1/api/chat", json=payload, headers=auth_headers) as response:
        assert response.status_code == 200
        chunks = [__import__("json").loads(line) for line in response.iter_lines() if line]

    assert all(c["usage"] is None for c in chunks if not c["done"])
    final_chunk = next(c for c in chunks if c["done"])
    assert final_chunk["usage"]["prompt_tokens"] > 0
    assert final_chunk["usage"]["completion_tokens"] > 0


def test_chat_model_not_in_allow_list_is_rejected(client, auth_headers):
    original = settings.allowed_models
    settings.allowed_models = ["mock/allowed-model"]
    try:
        payload = {
            "model": "mock/not-allowed",
            "messages": [{"role": "user", "content": "hej"}],
        }
        response = client.post("/v1/api/chat", json=payload, headers=auth_headers)
        assert response.status_code == 400
    finally:
        settings.allowed_models = original


def test_chat_model_in_allow_list_is_accepted(client, auth_headers):
    original = settings.allowed_models
    settings.allowed_models = ["mock/allowed-model"]
    try:
        payload = {
            "model": "mock/allowed-model",
            "messages": [{"role": "user", "content": "hej"}],
        }
        response = client.post("/v1/api/chat", json=payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["model"] == "mock/allowed-model"
    finally:
        settings.allowed_models = original
