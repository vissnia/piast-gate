from pydantic import BaseModel
from typing import List, Literal, Optional

class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 500