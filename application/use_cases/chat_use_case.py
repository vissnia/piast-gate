import time
import uuid
from typing import Dict
from domain.entities.pii_token import PIIToken
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
        state_type_counters: Dict[str, int] = {}
        state_value_to_token_str: Dict[str, str] = {}
        global_mapping: Dict[str, PIIToken] = {}
        
        anonymized_messages = []
        for msg in request.messages:
            anon_content, mapping = await self.anonymizer.anonymize_async(
                msg.content, 
                state_type_counters, 
                state_value_to_token_str
            )
            global_mapping.update(mapping)
            anonymized_messages.append({"role": msg.role, "content": anon_content})

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
