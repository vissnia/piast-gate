from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    prompt: str

class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    response: str
