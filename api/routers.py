import logging
from fastapi import APIRouter, Depends, HTTPException

from application.dtos.chat_request import ChatRequest
from application.dtos.chat_response import ChatResponse
from application.use_cases.chat_use_case import ChatUseCase
from api.di.chat_container import get_chat_use_case

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=200,
    summary="Process a chat request",
    description="Anonymizes input, sends to LLM, and deanonymizes response."
)
async def chat_endpoint(
    request: ChatRequest,
    use_case: ChatUseCase = Depends(get_chat_use_case)
):
    """
    Endpoint for chat interactions.

    Args:
        request (ChatRequest): The user's chat message.
        use_case (ChatUseCase): Injected application core logic.

    Returns:
        ChatResponse: The LLM's response.
    """
    try:
        response = await use_case.execute(request)
        return response
    except ValueError as e:
        logger.warning(f"Validation error in chat endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An internal server error occurred processing the request."
        )
