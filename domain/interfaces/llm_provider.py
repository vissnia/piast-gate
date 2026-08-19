from typing import Any, AsyncIterator, List, Optional, Protocol

from domain.entities.llm_response import LLMResponse
from domain.entities.stream_delta import StreamDelta


class LLMProvider(Protocol):
    """Interface for LLM interactions."""

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        """
        Sends a conversation to the LLM and returns the full response.

        Args:
            messages (list[dict]): The conversation messages (should be anonymized).
            model (str): The model to route to (provider-prefixed, e.g. "gemini/gemini-2.5-flash").
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum tokens to generate.
            top_p, stop, presence_penalty, frequency_penalty, seed: Optional sampling params,
                forwarded to the provider only when set.
            tools, tool_choice, response_format: Optional passthrough params for function
                calling / structured output.

        Returns:
            LLMResponse: The LLM's complete response.
        """
        ...

    async def chat_stream(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[dict] = None,
    ) -> AsyncIterator[StreamDelta]:
        """
        Sends a conversation to the LLM and streams the response chunk by chunk.

        Args:
            Same as :meth:`chat`.

        Yields:
            StreamDelta: Individual chunks from the LLM stream.
        """
        ...
        yield StreamDelta()
