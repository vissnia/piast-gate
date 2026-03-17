import time
import uuid
from typing import AsyncIterator, Dict
from application.dtos.chat_request import ChatRequest
from application.dtos.stream_chat_chunk import StreamChatChunk, StreamChoice, StreamDelta
from application.stream_deanonymizer import StreamDeanonymizer
from domain.entities.pii_token import PIIToken
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

    async def execute(self, request: ChatRequest) -> AsyncIterator[StreamChatChunk]:
        """
        Processes a streaming chat request end-to-end.

        Args:
            request (ChatRequest): The incoming chat request (``stream`` must be True).

        Yields:
            StreamChatChunk: Individual SSE chunks with de-anonymized content,
                             followed by a terminal chunk with ``finish_reason="stop"``.
        """
        state_type_counters: Dict[str, int] = {}
        state_value_to_token_str: Dict[str, str] = {}
        global_mapping: Dict[str, PIIToken] = {}

        anonymized_messages = []
        for msg in request.messages:
            anon_content, mapping = await self.anonymizer.anonymize_async(
                msg.content,
                state_type_counters,
                state_value_to_token_str,
            )
            global_mapping.update(mapping)
            anonymized_messages.append({"role": msg.role, "content": anon_content})

        raw_stream: AsyncIterator[str] = self.llm.chat_stream(
            messages=anonymized_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        deanonymizer = StreamDeanonymizer(mapping=global_mapping)
        chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())

        async for safe_text in deanonymizer.process(raw_stream):
            yield StreamChatChunk(
                id=chunk_id,
                created=created,
                model=request.model,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=StreamDelta(content=safe_text),
                        finish_reason=None,
                    )
                ],
            )

        yield StreamChatChunk(
            id=chunk_id,
            created=created,
            model=request.model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=StreamDelta(),
                    finish_reason="stop",
                )
            ],
        )
