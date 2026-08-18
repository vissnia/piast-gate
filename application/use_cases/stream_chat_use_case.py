from application.dtos.chat_response import ChatUsage
from application.helpers.stream_helper import build_chunk
from application.services.hallucination_scrubber import HallucinationScrubber
from application.services.message_anonymizer import anonymize_messages
from application.services.model_resolver import resolve_model
from application.services.thinking_parser import ThinkingParser
from typing import AsyncIterator, Dict, Optional
from application.dtos.chat_request import ChatRequest
from application.dtos.stream_chat_chunk import StreamChatChunk
from application.services.stream_deanonymizer import StreamDeanonymizer
from domain.entities.stream_delta import StreamDelta
from domain.entities.usage import Usage
from domain.interfaces.llm_provider import LLMProvider
from domain.services.anonymizer_service import AnonymizerService

class StreamChatUseCase:
    """
    Orchestrates the streaming chat flow with anonymization guarantees.

    Steps:
    1. Anonymize all user messages (same stateful mapping as non-streaming path).
    2. Open a streaming connection to the LLM.
    3. Pipe the LLM's text deltas through :class:`HallucinationScrubber` to
       redact any hallucinated PII, then through :class:`StreamDeanonymizer`
       to restore the real placeholders. Tool-call deltas bypass this
       text pipeline entirely (not scanned for PII in this version) and are
       accumulated separately, emitted as one chunk once the stream ends.
    4. Yield :class:`StreamChatChunk` objects ready to be serialised as SSE.
    """

    def __init__(self, anonymizer: AnonymizerService, llm: LLMProvider, hallucination_guard: AnonymizerService) -> None:
        """
        Args:
            anonymizer (AnonymizerService): Service that handles PII anonymization / de-anonymization.
            llm (LLMProvider): LLM provider that supports ``chat_stream``.
            hallucination_guard (AnonymizerService): Scoped to fast, non-NER
                detectors only; used to scrub hallucinated PII from the raw
                stream without the latency of running NER per word.
        """
        self.anonymizer = anonymizer
        self.llm = llm
        self.hallucination_guard = hallucination_guard

    @staticmethod
    async def _text_only(
        stream: AsyncIterator[StreamDelta],
        tool_call_fragments: Dict[int, dict],
        usage_holder: Dict[str, Optional[Usage]],
    ) -> AsyncIterator[str]:
        """
        Yields only the text content of each delta, harvesting any
        tool-call-delta fragments into ``tool_call_fragments`` (keyed by
        index, per litellm's streaming convention) and the final usage
        report (if any) into ``usage_holder["usage"]``, as a side effect.
        """
        async for delta in stream:
            for tcd in delta.tool_call_deltas or []:
                entry = tool_call_fragments.setdefault(tcd.index, {"id": "", "name": "", "arguments": ""})
                if tcd.id:
                    entry["id"] = tcd.id
                if tcd.name:
                    entry["name"] = tcd.name
                entry["arguments"] += tcd.arguments_fragment
            if delta.usage is not None:
                usage_holder["usage"] = delta.usage
            if delta.content:
                yield delta.content

    async def execute(self, request: ChatRequest) -> AsyncIterator[StreamChatChunk]:
        model = resolve_model(request.model)
        anonymized_messages, global_mapping = await anonymize_messages(self.anonymizer, request.messages)

        raw_stream = self.llm.chat_stream(
            messages=anonymized_messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stop=request.stop,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            seed=request.seed,
            tools=request.tools,
            tool_choice=request.tool_choice,
            response_format=request.response_format,
        )

        tool_call_fragments: Dict[int, dict] = {}
        usage_holder: Dict[str, Optional[Usage]] = {"usage": None}

        scrubber = HallucinationScrubber(self.hallucination_guard)
        deanonymizer = StreamDeanonymizer(mapping=global_mapping)
        parser = ThinkingParser()

        text_stream = self._text_only(raw_stream, tool_call_fragments, usage_holder)
        scrubbed_stream = scrubber.process(text_stream)
        async for safe_text in deanonymizer.process(scrubbed_stream):
            chunks = parser.process(safe_text)

            for content, thinking in chunks:
                yield build_chunk(request, content, thinking, done=False, model=model)

        if tool_call_fragments:
            tool_calls = [
                {"id": f["id"], "type": "function", "function": {"name": f["name"], "arguments": f["arguments"]}}
                for f in tool_call_fragments.values()
            ]
            yield build_chunk(request, "", "", done=False, tool_calls=tool_calls, model=model)

        usage = usage_holder["usage"]
        final_usage = ChatUsage(
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )
        yield build_chunk(request, "", "", done=True, model=model, usage=final_usage)
