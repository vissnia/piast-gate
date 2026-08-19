import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from api.config.auth import verify_api_key
from api.config.config import settings
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

async def _stream_generator(request: ChatRequest, use_case: StreamChatUseCase):
    """
    Serialises StreamChatChunk objects as OpenAI-compatible Server-Sent
    Events, so both generic SSE clients and OpenAI SDK-style streaming
    clients can consume the same endpoint.
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
    if request.stream:
        return StreamingResponse(
            _stream_generator(request, stream_use_case),
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
    return await use_case.execute(request)

@router.post(
    "/anonymize",
    response_model=AnonymizeResponse,
    status_code=200,
    summary="Anonymize a document (PDF or DOCX)",
    description="Accepts a file, anonymizes it, and returns the extracted content as anonymized markdown text.",
    dependencies=[Depends(verify_api_key)]
)
async def anonymize_document_endpoint(
    file: UploadFile = File(...),
    use_case: AnonymizeDocumentUseCase = Depends(get_anonymize_document_use_case)
):
    if file.size and file.size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Max size is {settings.max_upload_size / (1024 * 1024):.1f}MB."
        )

    content = await file.read()
    anonymized_text = await use_case.execute(content, file.content_type)

    return AnonymizeResponse(anonymized_text=anonymized_text)

@router.get("/tags")
def get_models():
    return {
        "models": [
            {
                "name": "piast-gate",
                "model": "piast-gate"
            }
        ]
    }
    