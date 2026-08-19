import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api.config.config import settings

logger = logging.getLogger(__name__)

_MULTIPART_OVERHEAD_ALLOWANCE = 64 * 1024


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """
    Rejects a request whose declared Content-Length grossly exceeds
    settings.max_upload_size before its body is read, so an oversized
    request is refused immediately instead of first being fully buffered
    by the JSON/multipart parser further down the stack.

    This only catches requests that declare Content-Length (as virtually
    all HTTP clients and browsers do). A request that omits it (e.g.
    chunked transfer-encoding) is not caught here; the endpoint-level
    check in api/routers.py, which inspects the fully-received
    UploadFile.size, remains the backstop for that case.
    """

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = None

            configured_limit = settings.max_upload_size
            max_body_size = configured_limit + _MULTIPART_OVERHEAD_ALLOWANCE
            if declared_size is not None and declared_size > max_body_size:
                logger.warning(
                    "Rejected request with Content-Length=%s exceeding max body size=%s | Path: %s",
                    declared_size, max_body_size, request.url.path,
                )
                return JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={
                        "error": {
                            "code": status.HTTP_413_CONTENT_TOO_LARGE,
                            "message": f"Request body too large. Max size is {configured_limit / (1024 * 1024):.1f}MB.",
                        }
                    },
                )

        return await call_next(request)
