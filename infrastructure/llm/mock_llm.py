import asyncio
from domain.interfaces.llm_provider import LLMProvider

class MockLLM(LLMProvider):
    """Mock implementation of an LLM provider."""

    async def chat(self, prompt: str) -> str:
        await asyncio.sleep(0.5)
        return f"LLM response to: {prompt}"
