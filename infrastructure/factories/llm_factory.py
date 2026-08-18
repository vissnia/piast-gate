from infrastructure.llm.mock_llm import MockLLM
from infrastructure.llm.litellm_provider import LiteLLMProvider
from domain.interfaces.llm_provider import LLMProvider
from api.config.config import settings

def create_llm_provider() -> LLMProvider:
    """
    Creates and returns an LLM provider based on environment configuration.

    Returns:
        LLMProvider: The configured LLM provider instance.

    Raises:
        ValueError: If configuration is invalid.
    """
    provider_type = settings.llm_provider.lower()

    if provider_type == "mock":
        return MockLLM()

    if provider_type == "litellm":
        return LiteLLMProvider()

    raise ValueError(f"Unknown LLM provider: {provider_type}")
