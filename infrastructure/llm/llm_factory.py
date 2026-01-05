import os
from infrastructure.llm.mock_llm import MockLLM
from infrastructure.llm.gemini_llm import GeminiLLM
from domain.interfaces.llm_provider import LLMProvider

def create_llm_provider() -> LLMProvider:
    """
    Creates and returns an LLM provider based on environment configuration.
    
    Returns:
        LLMProvider: The configured LLM provider instance.
        
    Raises:
        ValueError: If configuration is invalid.
    """
    provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_type == "mock":
        return MockLLM()
    
    if provider_type == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required for Gemini provider")
        
        model_name = os.getenv("MODEL_NAME")
        if not model_name:
            raise ValueError("MODEL_NAME environment variable is required for Gemini provider")
       
        return GeminiLLM(api_key, model_name)
        
    # Future providers (OpenAI, Azure) would be added here
    
    raise ValueError(f"Unknown LLM provider: {provider_type}")
