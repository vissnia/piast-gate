import pytest
from unittest.mock import MagicMock, patch
from infrastructure.llm.gemini_llm import GeminiLLM

@pytest.mark.asyncio
async def test_gemini_llm_chat():
    """Test GeminiLLM chat method with mocking."""
    api_key = "fake_key"
    model_name = "gemini-1.5-flash"
    
    mock_response = MagicMock()
    mock_response.text = "Hello token <PII:EMAIL:1>"
    
    with patch("infrastructure.llm.gemini_llm.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.return_value = mock_response
        
        gemini = GeminiLLM(api_key, model_name)
        response = await gemini.chat("Test prompt")
        
        assert response == "Hello token <PII:EMAIL:1>"
        
        # Verify system prompt inclusion
        call_args = mock_client.models.generate_content.call_args
        sent_contents = call_args.kwargs["contents"]
        assert "IMPORTANT: You are part of a PII scrubbing system." in sent_contents
        assert "User: Test prompt" in sent_contents

@pytest.mark.asyncio
async def test_gemini_llm_error():
    """Test GeminiLLM error handling."""
    api_key = "fake_key"
    model_name = "gemini-1.5-flash"
    
    with patch("infrastructure.llm.gemini_llm.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        gemini = GeminiLLM(api_key, model_name)
        with pytest.raises(RuntimeError, match="Gemini API error: API Error"):
            await gemini.chat("Test prompt")
