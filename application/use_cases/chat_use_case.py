from domain.interfaces.llm_provider import LLMProvider
from domain.services.anonymizer_service import AnonymizerService
from application.dtos.chat_request import ChatRequest
from application.dtos.chat_response import ChatResponse

class ChatUseCase:
    """Orchestrates the chat flow with anonymization."""

    def __init__(self, anonymizer: AnonymizerService, llm: LLMProvider):
        self.anonymizer = anonymizer
        self.llm = llm

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a chat request:
        1. Anonymize user prompt.
        2. Send to LLM.
        3. Deanonymize LLM response.
        4. Return result.
        """
        anon_prompt, mapping = self.anonymizer.anonymize(request.prompt)
        print("Anonymized prompt:", anon_prompt)

        llm_response_text = await self.llm.chat(anon_prompt)
        print("LLM response:", llm_response_text)
        
        final_response_text = self.anonymizer.deanonymize(llm_response_text, mapping)
        
        return ChatResponse(response=final_response_text)
