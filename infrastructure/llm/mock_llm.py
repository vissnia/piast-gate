import asyncio
from domain.interfaces.llm_provider import LLMProvider

class MockLLM(LLMProvider):
    """Mock implementation of an LLM provider."""

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 500) -> str:
        await asyncio.sleep(0.1)

        last_msg_content = messages[-1]["content"] if messages else ""
        return last_msg_content
