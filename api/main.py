from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from api.routers import router
from infrastructure.detectors.presidio_detector import download_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure model is downloaded on startup
    model_name = os.getenv("PL_NER_MODEL_NAME", "pl_core_news_lg")
    download_model(model_name)
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="LLM PII Gateway", version="0.1.0", lifespan=lifespan)
    
    app.include_router(router)
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
        
    return app
