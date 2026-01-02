import asyncio
from domain.interfaces import LLMProvider

class MockLLM(LLMProvider):
    """Mock implementation of an LLM provider."""

    async def chat(self, prompt: str) -> str:
        # Simulate network delay
        await asyncio.sleep(0.5)
        # return echo response
        return f"LLM response to: {prompt}"
