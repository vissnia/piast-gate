import asyncio
from typing import Any, AsyncIterator, List, Optional

from domain.entities.llm_response import LLMResponse, ToolCall
from domain.entities.stream_delta import StreamDelta, ToolCallDelta
from domain.entities.usage import Usage
from domain.interfaces.llm_provider import LLMProvider

_TOOL_CALL_TRIGGER = "__TRIGGER_TOOL_CALL__"


def _mock_tool_call() -> ToolCall:
    return ToolCall(id="mock-1", name="mock_tool", arguments='{"foo":"bar"}')


def _as_text(content) -> str:
    """Extracts a plain-text echo from a message's content, same as a real
    provider would only ever return text (never a content-part list)."""
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if part.get("type") == "text")
    return content or ""


def _approx_tokens(text: str) -> int:
    """Whitespace word count, used as a deterministic stand-in for a real
    tokenizer — good enough to exercise usage plumbing offline, not a token count."""
    return len(text.split())


def _mock_usage(messages: list[dict], completion_text: str) -> Usage:
    prompt_tokens = sum(_approx_tokens(_as_text(m.get("content"))) for m in messages)
    completion_tokens = _approx_tokens(completion_text)
    return Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


class MockLLM(LLMProvider):
    """Mock implementation of an LLM provider for local development and testing."""

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
        Returns the last message content as the response, unless it is the
        tool-call test sentinel, in which case a canned tool call is
        returned instead (deterministic, offline exercise of the
        tool-calling pass-through path).
        """
        await asyncio.sleep(0.1)
        last_msg_content = _as_text(messages[-1]["content"]) if messages else ""

        if last_msg_content == _TOOL_CALL_TRIGGER:
            return LLMResponse(
                content=None,
                tool_calls=[_mock_tool_call()],
                finish_reason="tool_calls",
                usage=_mock_usage(messages, ""),
            )

        return LLMResponse(content=last_msg_content, usage=_mock_usage(messages, last_msg_content))

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
        Streams the last message content word by word with a short delay,
        or a single canned tool-call delta for the test sentinel.
        """
        last_msg_content = _as_text(messages[-1]["content"]) if messages else ""

        if last_msg_content == _TOOL_CALL_TRIGGER:
            tc = _mock_tool_call()
            yield StreamDelta(
                tool_call_deltas=[ToolCallDelta(index=0, id=tc.id, name=tc.name, arguments_fragment=tc.arguments)],
                finish_reason="tool_calls",
            )
            yield StreamDelta(usage=_mock_usage(messages, ""))
            return

        words = last_msg_content.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(0.05)
            yield StreamDelta(content=word if i == 0 else f" {word}")

        yield StreamDelta(usage=_mock_usage(messages, last_msg_content))
