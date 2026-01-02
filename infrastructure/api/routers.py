from fastapi import APIRouter, Depends, HTTPException
from application.dtos import ChatRequest, ChatResponse
from application.use_cases import ChatUseCase
from infrastructure.detectors.regex_detector import RegexPIIDetector
from infrastructure.llm.mock_llm import MockLLM
from domain.services import AnonymizerService

router = APIRouter()

# Dependency Injection Factory
# For MVP we can instantiate here or use a proper DI container helper
# Since we need a fresh object or stateless service, let's create it.
# Ideally, we should use `lru_cache` or a global instance.

def get_chat_use_case() -> ChatUseCase:
    detectors = [RegexPIIDetector()]
    anonymizer = AnonymizerService(detectors)
    llm = MockLLM()
    return ChatUseCase(anonymizer, llm)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    use_case: ChatUseCase = Depends(get_chat_use_case)
):
    try:
        return await use_case.execute(request)
    except Exception as e:
        # Log error in production
        raise HTTPException(status_code=500, detail=str(e))
