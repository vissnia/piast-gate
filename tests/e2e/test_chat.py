def test_chat_success(client, auth_headers):
    """Test successful chat interaction with anonymization and deanonymization."""
    payload = {
        "prompt": "Nazywam się Jan Kowalski. Mój PESEL to 90010112345."
    }
    response = client.post("/chat", json=payload, headers=auth_headers)
    data = response.json()
    
    assert response.status_code == 200
    assert "response" in data
    assert "90010112345" in data["response"]
    assert "Jan Kowalski" in data["response"]


def test_chat_unauthorized(client):
    """Test chat without API key fails with 401."""
    payload = {"prompt": "Test"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 401
    
def test_chat_validation_error(client, auth_headers):
    """Test chat with invalid payload fails."""
    response = client.post("/chat", json={}, headers=auth_headers)
    assert response.status_code == 422
