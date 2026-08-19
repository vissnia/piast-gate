from typing import Any, AsyncIterator, List, Optional

import litellm
from litellm.exceptions import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    ContextWindowExceededError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from api.config.config import settings
from domain.entities.llm_response import LLMResponse, ToolCall
from domain.entities.stream_delta import StreamDelta, ToolCallDelta
from domain.entities.usage import Usage
from domain.exceptions.llm_provider_error import LLMProviderError
from domain.interfaces.llm_provider import LLMProvider


def _map_usage(raw_usage) -> Optional[Usage]:
    if raw_usage is None:
        return None
    return Usage(
        prompt_tokens=getattr(raw_usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(raw_usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(raw_usage, "total_tokens", 0) or 0,
    )

_PROXY_MODEL_PREFIX = "litellm_proxy/"

_LITELLM_EXCEPTIONS = (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    APIConnectionError,
    ServiceUnavailableError,
    Timeout,
    ContextWindowExceededError,
    NotFoundError,
)


class LiteLLMProvider(LLMProvider):
    """LLM provider implementation backed by litellm, routing to whichever
    provider the given ``model`` string prefix selects. Two modes coexist,
    selected per-call by the model prefix alone — no separate provider/mode
    setting is needed:

    - Direct-to-provider (e.g. "gemini/gemini-2.5-flash", "openai/gpt-4o",
      "anthropic/claude-...") — litellm calls the provider's API directly,
      reading that provider's API key straight from the environment
      (GEMINI_API_KEY, OPENAI_API_KEY, ...).
    - Via an externally-hosted LiteLLM Proxy (e.g. "litellm_proxy/gpt-4o",
      where the suffix is whatever alias the proxy's own config exposes) —
      litellm instead calls that proxy's OpenAI-compatible endpoint, using
      ``settings.litellm_proxy_api_base``/``litellm_proxy_api_key`` (a
      virtual key issued by the proxy, not a real provider key).

    Both modes can be used side by side in the same deployment; which one
    applies is decided per-request by whatever model string is resolved.
    """

    _SYSTEM_PROMPT = (
        "IMPORTANT: You are part of a PII scrubbing system.\n"
        "User prompts may contain anonymized tokens like <PII_TYPE_AND_ID_NUMBER>.\n"
        "YOU MUST PRESERVE THESE TOKENS EXACTLY IN YOUR RESPONSE.\n"
        "DO NOT modify, rename, or obfuscate them."
    )

    def _build_messages(self, messages: list[dict]) -> list[dict]:
        return [{"role": "system", "content": self._SYSTEM_PROMPT}, *messages]

    def _build_kwargs(
        self,
        model: str,
        top_p: Optional[float],
        stop: Optional[List[str]],
        presence_penalty: Optional[float],
        frequency_penalty: Optional[float],
        seed: Optional[int],
        tools: Optional[List[dict]],
        tool_choice: Optional[Any],
        response_format: Optional[dict],
    ) -> dict:
        candidate = {
            "top_p": top_p,
            "stop": stop,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "seed": seed,
            "tools": tools,
            "tool_choice": tool_choice,
            "response_format": response_format,
        }
        if model.startswith(_PROXY_MODEL_PREFIX):
            candidate["api_base"] = settings.litellm_proxy_api_base
            candidate["api_key"] = settings.litellm_proxy_api_key
        return {k: v for k, v in candidate.items() if v is not None}

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
        try:
            response = await litellm.acompletion(
                model=model,
                messages=self._build_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                num_retries=settings.llm_num_retries,
                **self._build_kwargs(
                    model, top_p, stop, presence_penalty, frequency_penalty,
                    seed, tools, tool_choice, response_format,
                ),
            )
        except _LITELLM_EXCEPTIONS as e:
            raise LLMProviderError(str(e.message), e.status_code or 502) from e

        choice = response.choices[0]
        msg = choice.message

        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments)
                for tc in msg.tool_calls
            ]

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=_map_usage(getattr(response, "usage", None)),
        )

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
        try:
            stream = await litellm.acompletion(
                model=model,
                messages=self._build_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                num_retries=settings.llm_num_retries,
                stream=True,
                stream_options={"include_usage": True},
                **self._build_kwargs(
                    model, top_p, stop, presence_penalty, frequency_penalty,
                    seed, tools, tool_choice, response_format,
                ),
            )

            async for chunk in stream:
                usage = _map_usage(getattr(chunk, "usage", None))

                if not chunk.choices:
                    if usage is not None:
                        yield StreamDelta(usage=usage)
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                tool_call_deltas = None
                if delta.tool_calls:
                    tool_call_deltas = [
                        ToolCallDelta(
                            index=tc.index,
                            id=tc.id,
                            name=tc.function.name if tc.function else None,
                            arguments_fragment=(tc.function.arguments if tc.function else "") or "",
                        )
                        for tc in delta.tool_calls
                    ]

                yield StreamDelta(
                    content=delta.content or "",
                    tool_call_deltas=tool_call_deltas,
                    finish_reason=choice.finish_reason,
                    usage=usage,
                )
        except _LITELLM_EXCEPTIONS as e:
            raise LLMProviderError(str(e.message), e.status_code or 502) from e
