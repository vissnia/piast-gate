def test_chat_success(client, auth_headers):
    """Test successful chat interaction with anonymization and deanonymization."""
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": "Nazywam się Jan Kowalski. Mój PESEL to 90010112349."
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    response = client.post("/v1/api/chat", json=payload, headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    assert "choices" in data
    assert "message" in data["choices"][0]
    assert "content" in data["choices"][0]["message"]
    assert "90010112349" in data["choices"][0]["message"]["content"]
    assert "Jan Kowalski" in data["choices"][0]["message"]["content"]


def test_chat_unauthorized(client):
    """Test chat without API key fails with 401."""
    payload = {"prompt": "Test"}
    response = client.post("/v1/api/chat", json=payload)
    
    assert response.status_code == 401
    
def test_chat_validation_error(client, auth_headers):
    """Test chat with invalid payload fails."""
    response = client.post("/v1/api/chat", json={}, headers=auth_headers)
    assert response.status_code == 422

def test_chat_streaming_success(client, auth_headers, parse_sse_chunks):
    """Test successful streaming chat interaction with anonymization and deanonymization."""
    payload = {
        "model": "gemini-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": "Nazywam się Jan Kowalski. Mój numer to 500123456."
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "stream": True,
    }

    with client.stream("POST", "/v1/api/chat", json=payload, headers=auth_headers) as response:
        assert response.status_code == 200
        chunks = parse_sse_chunks(response)

        assert len(chunks) > 0

        full_content = ""
        for chunk in chunks:
            assert "choices" in chunk
            if not chunk["choices"]:
                continue
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                full_content += delta["content"]

        assert "500123456" in full_content
        assert "Jan Kowalski" in full_content
