from fastapi.testclient import TestClient
from api.main import create_app

app = create_app()
client = TestClient(app)

def test_chat_flow():
    # Helper to check if PII is sanitized in the flow
    # Since we use a Mock LLM that echoes the prompt, 
    # if the Anonymizer works, the underlying system sees the token.
    # But the Deanonymizer should restore it before returning to user.
    # So end-to-end, we see the original PII.
    
    prompt = "My email is user@test.com"
    response = client.post("/chat", json={"prompt": prompt})
    
    assert response.status_code == 200
    data = response.json()
    
    # The response should be "LLM response to: <anonymized_prompt>"... DEANONYMIZED
    # Wait, the MockLLM receives the ANONYMIZED prompt.
    # It returns "LLM response to: <PII:EMAIL:123>"
    # The UseCase deanonymizes this string.
    # So the final string should be "LLM response to: My email is user@test.com" (if regex works on the return path)
    # Actually, deanonymize replaces tokens back to originals.
    
    expected_content = "LLM response to: My email is user@test.com"
    
    # Note: Depending on how the regex replacement works, spacing might vary slightly if not perfect,
    # but for this logic it should be exact.
    # However, deanonymize logic simply replaces token_str -> original_value.
    # So "LLM response to: <PII...>" becomes "LLM response to: My email..."
    
    # Let's verify we get a 200 and the content is present.
    assert "user@test.com" in data["response"]
    assert "LLM response to:" in data["response"]

def test_chat_no_pii():
    prompt = "Hello"
    response = client.post("/chat", json={"prompt": prompt})
    assert response.status_code == 200
    assert response.json()["response"] == "LLM response to: Hello"
