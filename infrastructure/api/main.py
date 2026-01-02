from fastapi import FastAPI
from infrastructure.api.routers import router

def create_app() -> FastAPI:
    app = FastAPI(title="LLM PII Gateway", version="0.1.0")
    
    app.include_router(router)
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
        
    return app
