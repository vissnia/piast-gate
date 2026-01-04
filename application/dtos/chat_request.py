from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    prompt: str