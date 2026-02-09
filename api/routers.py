from api.config.auth import verify_api_key
import logging
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response

from application.dtos.chat_request import ChatRequest
from application.dtos.chat_response import ChatResponse
from application.dtos.anonymize_request import AnonymizeRequest
from application.dtos.anonymize_response import AnonymizeResponse
from application.use_cases.chat_use_case import ChatUseCase
from application.use_cases.anonymize_use_case import AnonymizeUseCase
from application.use_cases.anonymize_document_use_case import AnonymizeDocumentUseCase
from api.di.chat_container import get_chat_use_case, get_anonymize_use_case
from api.di.document_container import get_anonymize_document_use_case

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=200,
    summary="Process a chat request",
    description="Anonymizes input, sends to LLM, and deanonymizes response.",
    dependencies=[Depends(verify_api_key)]
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

@router.post(
    "/anonymize/text",
    response_model=AnonymizeResponse,
    status_code=200,
    summary="Anonymize text without LLM processing",
    description="Anonymizes input text and returns the result.",
    dependencies=[Depends(verify_api_key)]
)
async def anonymize_text_endpoint(
    request: AnonymizeRequest,
    use_case: AnonymizeUseCase = Depends(get_anonymize_use_case)
):
    """
    Endpoint for text anonymization.

    Args:
        request (AnonymizeRequest): The user's text to anonymize.
        use_case (AnonymizeUseCase): Injected application core logic.

    Returns:
        AnonymizeResponse: The anonymized text.
    """
    try:
        response = await use_case.execute(request)
        return response
    except ValueError as e:
        logger.warning(f"Validation error in anonymize endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in anonymize endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An internal server error occurred processing the request."
        )

@router.post(
    "/anonymize",
    status_code=200,
    summary="Anonymize a document (PDF or DOCX)",
    description="Accepts a file, anonymizes it, and returns the processed file.",
    dependencies=[Depends(verify_api_key)]
)
async def anonymize_document_endpoint(
    file: UploadFile = File(...),
    use_case: AnonymizeDocumentUseCase = Depends(get_anonymize_document_use_case)
):
    """
    Endpoint for document anonymization.

    Args:
        file (UploadFile): The file to anonymize.
        use_case (AnonymizeDocumentUseCase): Injected application core logic.

    Returns:
        Response: The anonymized file content.
    """
    try:
        content = await file.read()
        anonymized_content = await use_case.execute(content, file.content_type)
        
        filename = f"anonymized_{file.filename}"
        content_disposition = f"attachment; filename*=UTF-8''{quote(filename)}"
        return Response(
            content=anonymized_content,
            media_type=file.content_type,
            headers={"Content-Disposition": content_disposition}
        )
    except ValueError as e:
        logger.warning(f"Validation error in document anonymize endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in document anonymize endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An internal server error occurred processing the request."
        )
