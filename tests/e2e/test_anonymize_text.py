def test_anonymize_text_success(client, auth_headers):
    """Test successful anonymization of text."""
    payload = {
        "text": "Jan Kowalski mieszka w Warszawie. Jego PESEL to 90010112345."
    }
    response = client.post("/anonymize/text", json=payload, headers=auth_headers)
    data = response.json()

    assert response.status_code == 200
    assert "anonymized_text" in data
    assert "90010112345" not in data["anonymized_text"]
    assert "Jan Kowalski" not in data["anonymized_text"]
    assert "Warszawie" not in data["anonymized_text"]
    assert "<PERSON" in data["anonymized_text"]
    assert "<PESEL" in data["anonymized_text"]
    assert "<LOCATION" in data["anonymized_text"]
    
def test_anonymize_text_unauthorized(client):
    """Test anonymization without API key fails with 401 Unauthorized."""
    payload = {
        "text": "Test unauthorized access."
    }
    response = client.post("/anonymize/text", json=payload)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API Key"
    
def test_anonymize_text_validation_error(client, auth_headers):
    """Test anonymization with invalid payload fails with 422 Unprocessable Entity."""
    response = client.post("/anonymize/text", json={}, headers=auth_headers)
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["loc"] == ["body", "text"]
    assert data["detail"][0]["msg"] == "Field required"
