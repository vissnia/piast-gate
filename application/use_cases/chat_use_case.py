import time
import uuid
from domain.interfaces.llm_provider import LLMProvider
from domain.services.anonymizer_service import AnonymizerService
from application.dtos.chat_request import ChatRequest
from application.dtos.chat_response import ChatResponse, ChatChoice, ChatChoiceMessage, ChatUsage

class ChatUseCase:
    """Orchestrates the chat flow with anonymization."""

    def __init__(self, anonymizer: AnonymizerService, llm: LLMProvider):
        self.anonymizer = anonymizer
        self.llm = llm

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a chat request:
        1. Anonymize user messages.
        2. Send to LLM.
        3. Deanonymize LLM response.
        4. Return formatted OpenAI compatible response.
        """
        texts = [msg.content for msg in request.messages]
        anonymized_texts, global_mapping = await self.anonymizer.anonymize_texts_async(texts)
        anonymized_messages = [
            {"role": msg.role, "content": anon_content}
            for msg, anon_content in zip(request.messages, anonymized_texts)
        ]

        llm_response_text = await self.llm.chat(
            messages=anonymized_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        final_response_text = await self.anonymizer.deanonymize_async(llm_response_text, global_mapping)
        
        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatChoiceMessage(
                        role="assistant",
                        content=final_response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=ChatUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        )
