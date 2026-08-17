from application.helpers.stream_helper import build_chunk
from application.services.thinking_parser import ThinkingParser
from typing import AsyncIterator
from application.dtos.chat_request import ChatRequest
from application.dtos.stream_chat_chunk import StreamChatChunk
from application.services.stream_deanonymizer import StreamDeanonymizer
from domain.interfaces.llm_provider import LLMProvider
from domain.services.anonymizer_service import AnonymizerService

class StreamChatUseCase:
    """
    Orchestrates the streaming chat flow with anonymization guarantees.

    Steps:
    1. Anonymize all user messages (same stateful mapping as non-streaming path).
    2. Open a streaming connection to the LLM.
    3. Pipe LLM chunks through :class:`StreamDeanonymizer` to restore PII.
    4. Yield :class:`StreamChatChunk` objects ready to be serialised as SSE.
    """

    def __init__(self, anonymizer: AnonymizerService, llm: LLMProvider) -> None:
        """
        Args:
            anonymizer (AnonymizerService): Service that handles PII anonymization / de-anonymization.
            llm (LLMProvider): LLM provider that supports ``chat_stream``.
        """
        self.anonymizer = anonymizer
        self.llm = llm

    async def _anonymize_messages(self, request: ChatRequest):
        texts = [msg.content for msg in request.messages]
        anonymized_texts, global_mapping = await self.anonymizer.anonymize_texts_async(texts)
        anonymized_messages = [
            {"role": msg.role, "content": anon_content}
            for msg, anon_content in zip(request.messages, anonymized_texts)
        ]

        return anonymized_messages, global_mapping

    async def execute(self, request: ChatRequest) -> AsyncIterator[StreamChatChunk]:
        anonymized_messages, global_mapping = await self._anonymize_messages(request)

        raw_stream = self.llm.chat_stream(
            messages=anonymized_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        deanonymizer = StreamDeanonymizer(mapping=global_mapping)
        parser = ThinkingParser()

        async for safe_text in deanonymizer.process(raw_stream):
            chunks = parser.process(safe_text)

            for content, thinking in chunks:
                yield build_chunk(request, content, thinking, done=False)

        yield build_chunk(request, "", "", done=True)
