import logging
from urllib.parse import quote
from fastapi import APIRouter, Depends, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from api.config.auth import verify_api_key
from application.dtos.chat_request import ChatRequest
from application.dtos.anonymize_request import AnonymizeRequest
from application.dtos.anonymize_response import AnonymizeResponse
from application.use_cases.chat_use_case import ChatUseCase
from application.use_cases.anonymize_use_case import AnonymizeUseCase
from application.use_cases.anonymize_document_use_case import AnonymizeDocumentUseCase
from application.use_cases.stream_chat_use_case import StreamChatUseCase
from api.di.chat_container import get_chat_use_case, get_anonymize_use_case, get_stream_chat_use_case
from api.di.document_container import get_anonymize_document_use_case

logger = logging.getLogger(__name__)

router = APIRouter()

async def _sse_generator(request: ChatRequest, use_case: StreamChatUseCase):
    """
    Async generator that serialises StreamChatChunk objects as SSE lines.

    Args:
        request (ChatRequest): The validated chat request.
        use_case (StreamChatUseCase): Injected streaming use case.

    Yields:
        str: SSE-formatted text lines.
    """
    async for chunk in use_case.execute(request):
        yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
    yield "data: [DONE]\n\n"


@router.post(
    "/chat",
    summary="Process a chat request",
    description=(
        "Anonymizes input, sends to LLM, and de-anonymizes the response. "
        "Set ``stream=true`` in the request body to receive a Server-Sent Events stream."
    ),
    dependencies=[Depends(verify_api_key)],
)
async def chat_endpoint(
    request: ChatRequest,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case),
    stream_use_case: StreamChatUseCase = Depends(get_stream_chat_use_case),
):
    """
    Unified chat endpoint supporting both streaming and non-streaming modes.

    Args:
        request (ChatRequest): The incoming chat request. Set ``stream=true`` to enable streaming.
        chat_use_case (ChatUseCase): Injected non-streaming use case (used when stream=False).
        stream_use_case (StreamChatUseCase): Injected streaming use case (used when stream=True).

    Returns:
        StreamingResponse | ChatResponse: SSE stream or complete JSON response.
    """
    if request.stream:
        return StreamingResponse(
            _sse_generator(request, stream_use_case),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return await chat_use_case.execute(request)


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
    return await use_case.execute(request)

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
    content = await file.read()
    anonymized_content = await use_case.execute(content, file.content_type)
    
    filename = f"anonymized_{file.filename}"
    content_disposition = f"attachment; filename*=UTF-8''{quote(filename)}"
    
    return Response(
        content=anonymized_content,
        media_type=file.content_type,
        headers={"Content-Disposition": content_disposition}
    )
