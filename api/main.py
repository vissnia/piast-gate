from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from api.routers import router
from api.config.limiter import limiter
from api.config.config import settings
from api.middleware.error_handler import GlobalErrorHandlerMiddleware
from api.config.logging_config import setup_logging

setup_logging()

def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM PII Gateway", 
        version="0.1.0",
    )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(GlobalErrorHandlerMiddleware)
    app.add_middleware(SlowAPIMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    app.include_router(router)
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
        
    return app
