import asyncio
from typing import AsyncIterator
from domain.interfaces.llm_provider import LLMProvider

class MockLLM(LLMProvider):
    """Mock implementation of an LLM provider for local development and testing."""

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Returns the last message content as the response.

        Args:
            messages (list[dict]): Conversation messages.
            temperature (float): Unused in mock.
            max_tokens (int): Unused in mock.

        Returns:
            str: Echo of the last user message.
        """
        await asyncio.sleep(0.1)
        last_msg_content = messages[-1]["content"] if messages else ""
        return last_msg_content

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AsyncIterator[str]:
        """
        Streams the last message content word by word with a short delay.

        Args:
            messages (list[dict]): Conversation messages.
            temperature (float): Unused in mock.
            max_tokens (int): Unused in mock.

        Yields:
            str: Individual words from the last user message with spaces preserved.
        """
        last_msg_content = messages[-1]["content"] if messages else ""
        words = last_msg_content.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(0.05)
            yield word if i == 0 else f" {word}"
