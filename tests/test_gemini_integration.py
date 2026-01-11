import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from api.main import create_app
import os

app = create_app()
client = TestClient(app)

def test_gemini_integration_flow():
    """
    Test the full chat flow using (mocked) Gemini LLM.
    Verifies that PII is anonymized before sending to Gemini and deanonymized in the response.
    """
    env_vars = {
        "LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "fake_key",
        "MODEL_NAME": "gemini-1.5-flash"
    }
    
    with patch.dict(os.environ, env_vars):
        user_prompt = "Rewrite the text below into a more formal one, without changing your email address: Write to me at joe.doe@example.com when you're ready."
        
        # The expected anonymized prompt that Gemini would see
        # Note: PESEL/Email/Phone detectors are active.
        # The Exact token depends on the mapping, but we can mock the Gemini call.
        
        def side_effect(contents, model):
            # Extract token from contents if possible, or just echo
            # For simplicity in test, let's just find the token and return it in a sentence
            import re
            token_match = re.search(r"(<PII:EMAIL:[a-f0-9]+>)", contents)
            token = token_match.group(1) if token_match else "<PII:EMAIL:MISSING>"
            mock_resp = MagicMock()
            mock_resp.text = f"Please contact me at {token} once you are prepared."
            return mock_resp

        with patch("infrastructure.llm.gemini_llm.genai.Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.models.generate_content.side_effect = side_effect
            
            response = client.post("/chat", json={"prompt": user_prompt})
            
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            
            # Verify the original email is back in the final response
            assert "joe.doe@example.com" in data["response"]
            assert "Please contact me at" in data["response"]
            
            # Verify generate_content was called with something containing a PII token
            call_args = mock_client.models.generate_content.call_args
            assert call_args, "generate_content was not called"
            sent_contents = call_args.kwargs["contents"]
            assert "<PII:EMAIL:" in sent_contents
            assert "joe.doe@example.com" not in sent_contents
