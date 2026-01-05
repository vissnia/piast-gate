from pydantic import BaseModel

class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    response: str