from asyncio.protocols import Protocol
from typing import AsyncIterator

class LLMProvider(Protocol):
    """Interface for LLM interactions."""

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Sends a conversation to the LLM and returns the full response.

        Args:
            messages (list[dict]): The conversation messages (should be anonymized).
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum tokens to generate.

        Returns:
            str: The LLM's complete response.
        """
        pass

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AsyncIterator[str]:
        """
        Sends a conversation to the LLM and streams the response token by token.

        Args:
            messages (list[dict]): The conversation messages (should be anonymized).
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum tokens to generate.

        Yields:
            str: Individual text chunks from the LLM stream.
        """
        yield ""
