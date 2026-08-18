import time
import uuid
from domain.interfaces.llm_provider import LLMProvider
from domain.services.anonymizer_service import AnonymizerService
from application.dtos.chat_request import ChatRequest
from application.dtos.chat_response import ChatResponse, ChatChoice, ChatChoiceMessage, ChatUsage
from application.services.message_anonymizer import anonymize_messages
from application.services.model_resolver import resolve_model

class ChatUseCase:
    """Orchestrates the chat flow with anonymization."""

    def __init__(self, anonymizer: AnonymizerService, llm: LLMProvider):
        self.anonymizer = anonymizer
        self.llm = llm

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a chat request:
        1. Resolve/validate the requested model.
        2. Anonymize user messages.
        3. Send to LLM.
        4. Deanonymize LLM response.
        5. Return formatted OpenAI compatible response.
        """
        model = resolve_model(request.model)
        anonymized_messages, global_mapping = await anonymize_messages(self.anonymizer, request.messages)

        llm_response = await self.llm.chat(
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

        final_content = None
        if llm_response.content is not None:
            safe_response_text, _ = await self.anonymizer.redact_async(llm_response.content)
            final_content = await self.anonymizer.deanonymize_async(safe_response_text, global_mapping)

        tool_calls = None
        if llm_response.tool_calls:
            tool_calls = [
                {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}
                for tc in llm_response.tool_calls
            ]

        usage = llm_response.usage

        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatChoiceMessage(
                        role="assistant",
                        content=final_content,
                        tool_calls=tool_calls,
                    ),
                    finish_reason=llm_response.finish_reason
                )
            ],
            usage=ChatUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            )
        )
