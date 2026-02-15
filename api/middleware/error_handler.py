import logging
import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from api.config.config import settings

logger = logging.getLogger(__name__)

class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            return await self._handle_exception(request, e)

    async def _handle_exception(self, request: Request, e: Exception) -> JSONResponse:
        error_details = None
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Internal Server Error"

        if isinstance(e, (StarletteHTTPException, RequestValidationError)):
            if isinstance(e, StarletteHTTPException):
                status_code = e.status_code
                message = e.detail
            elif isinstance(e, RequestValidationError):
                 status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                 message = "Validation Error"
                 error_details = e.errors()

            logger.warning(
                f"HTTP Exception: {message} | Status: {status_code} | Path: {request.url.path}"
            )
        else:
            logger.error(
                f"Unhandled Exception: {str(e)} | Path: {request.url.path}",
                exc_info=True
            )
            
            if settings.debug:
                 message = str(e)
                 error_details = traceback.format_exc()

        return JSONResponse(
            status_code=status_code,
            content=self._build_error_response(status_code, message, error_details),
        )

    def _build_error_response(
        self, status_code: int, message: str, details: Union[str, list, None] = None
    ) -> dict:
        response = {
            "error": {
                "code": status_code,
                "message": message,
            }
        }
        if details:
            response["error"]["details"] = details
        return response
