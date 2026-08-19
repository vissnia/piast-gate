import pytest
from types import SimpleNamespace

import litellm
from litellm.exceptions import AuthenticationError

from api.config.config import settings
from infrastructure.llm.litellm_provider import LiteLLMProvider
from domain.exceptions.llm_provider_error import LLMProviderError


def _tool_call(id_="call_1", name="get_weather", arguments='{"city":"Warsaw"}'):
    return SimpleNamespace(id=id_, function=SimpleNamespace(name=name, arguments=arguments))


def _model_response(content=None, tool_calls=None, finish_reason="stop", usage=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    response = SimpleNamespace(choices=[choice])
    if usage is not None:
        response.usage = usage
    return response


def _usage(prompt_tokens=10, completion_tokens=5, total_tokens=15):
    return SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens)


async def _stream_chunks(*chunks):
    for c in chunks:
        yield c


@pytest.fixture
def provider() -> LiteLLMProvider:
    return LiteLLMProvider()


@pytest.mark.asyncio
async def test_chat_maps_plain_text_response(monkeypatch, provider: LiteLLMProvider):
    async def fake_acompletion(**kwargs):
        assert kwargs["model"] == "gemini/gemini-2.5-flash"
        assert kwargs["messages"][0]["role"] == "system"
        return _model_response(content="Cześć!")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await provider.chat(messages=[{"role": "user", "content": "hej"}], model="gemini/gemini-2.5-flash")

    assert result.content == "Cześć!"
    assert result.tool_calls is None
    assert result.finish_reason == "stop"


@pytest.mark.asyncio
async def test_chat_maps_tool_calls(monkeypatch, provider: LiteLLMProvider):
    async def fake_acompletion(**kwargs):
        assert kwargs["tools"] == [{"type": "function", "function": {"name": "get_weather"}}]
        return _model_response(content=None, tool_calls=[_tool_call()], finish_reason="tool_calls")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await provider.chat(
        messages=[{"role": "user", "content": "pogoda?"}],
        model="openai/gpt-4o",
        tools=[{"type": "function", "function": {"name": "get_weather"}}],
    )

    assert result.content is None
    assert result.finish_reason == "tool_calls"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[0].arguments == '{"city":"Warsaw"}'


@pytest.mark.asyncio
async def test_chat_maps_usage(monkeypatch, provider: LiteLLMProvider):
    async def fake_acompletion(**kwargs):
        return _model_response(content="ok", usage=_usage(prompt_tokens=12, completion_tokens=7, total_tokens=19))

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await provider.chat(messages=[{"role": "user", "content": "hej"}], model="gemini/gemini-2.5-flash")

    assert result.usage.prompt_tokens == 12
    assert result.usage.completion_tokens == 7
    assert result.usage.total_tokens == 19


@pytest.mark.asyncio
async def test_chat_wraps_provider_errors(monkeypatch, provider: LiteLLMProvider):
    async def fake_acompletion(**kwargs):
        raise AuthenticationError(message="bad key", llm_provider="gemini", model="gemini-2.5-flash")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    with pytest.raises(LLMProviderError) as exc_info:
        await provider.chat(messages=[{"role": "user", "content": "hej"}], model="gemini/gemini-2.5-flash")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_chat_direct_provider_model_omits_proxy_kwargs(monkeypatch, provider: LiteLLMProvider):
    monkeypatch.setattr(settings, "litellm_proxy_api_base", "http://proxy.internal:4000")
    monkeypatch.setattr(settings, "litellm_proxy_api_key", "sk-proxy-key")

    async def fake_acompletion(**kwargs):
        assert "api_base" not in kwargs
        assert "api_key" not in kwargs
        return _model_response(content="ok")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    await provider.chat(messages=[{"role": "user", "content": "hej"}], model="gemini/gemini-2.5-flash")


@pytest.mark.asyncio
async def test_chat_proxy_model_passes_proxy_kwargs(monkeypatch, provider: LiteLLMProvider):
    monkeypatch.setattr(settings, "litellm_proxy_api_base", "http://proxy.internal:4000")
    monkeypatch.setattr(settings, "litellm_proxy_api_key", "sk-proxy-key")

    async def fake_acompletion(**kwargs):
        assert kwargs["model"] == "litellm_proxy/gpt-4o"
        assert kwargs["api_base"] == "http://proxy.internal:4000"
        assert kwargs["api_key"] == "sk-proxy-key"
        return _model_response(content="ok")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    await provider.chat(messages=[{"role": "user", "content": "hej"}], model="litellm_proxy/gpt-4o")


@pytest.mark.asyncio
async def test_chat_stream_maps_content_and_tool_call_deltas(monkeypatch, provider: LiteLLMProvider):
    delta1 = SimpleNamespace(content="Cześć", tool_calls=None)
    delta2 = SimpleNamespace(
        content=None,
        tool_calls=[SimpleNamespace(index=0, id="call_1", function=SimpleNamespace(name="get_weather", arguments='{"cit'))],
    )
    delta3 = SimpleNamespace(
        content=None,
        tool_calls=[SimpleNamespace(index=0, id=None, function=SimpleNamespace(name=None, arguments='y":"Warsaw"}'))],
    )
    chunk1 = SimpleNamespace(choices=[SimpleNamespace(delta=delta1, finish_reason=None)])
    chunk2 = SimpleNamespace(choices=[SimpleNamespace(delta=delta2, finish_reason=None)])
    chunk3 = SimpleNamespace(choices=[SimpleNamespace(delta=delta3, finish_reason="tool_calls")])

    async def fake_acompletion(**kwargs):
        assert kwargs["stream"] is True
        return _stream_chunks(chunk1, chunk2, chunk3)

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    deltas = [d async for d in provider.chat_stream(messages=[{"role": "user", "content": "hej"}], model="gemini/gemini-2.5-flash")]

    assert deltas[0].content == "Cześć"
    assert deltas[1].tool_call_deltas[0].id == "call_1"
    assert deltas[1].tool_call_deltas[0].arguments_fragment == '{"cit'
    assert deltas[2].tool_call_deltas[0].id is None
    assert deltas[2].tool_call_deltas[0].arguments_fragment == 'y":"Warsaw"}'
    assert deltas[2].finish_reason == "tool_calls"


@pytest.mark.asyncio
async def test_chat_stream_requests_and_maps_final_usage_chunk(monkeypatch, provider: LiteLLMProvider):
    content_delta = SimpleNamespace(content="Cześć", tool_calls=None)
    content_chunk = SimpleNamespace(choices=[SimpleNamespace(delta=content_delta, finish_reason=None)])
    usage_chunk = SimpleNamespace(choices=[], usage=_usage(prompt_tokens=8, completion_tokens=3, total_tokens=11))

    async def fake_acompletion(**kwargs):
        assert kwargs["stream_options"] == {"include_usage": True}
        return _stream_chunks(content_chunk, usage_chunk)

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    deltas = [d async for d in provider.chat_stream(messages=[{"role": "user", "content": "hej"}], model="gemini/gemini-2.5-flash")]

    assert deltas[0].content == "Cześć"
    assert deltas[0].usage is None
    assert deltas[1].content == ""
    assert deltas[1].usage.prompt_tokens == 8
    assert deltas[1].usage.completion_tokens == 3
    assert deltas[1].usage.total_tokens == 11
