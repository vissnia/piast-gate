from pydantic import BaseModel, Field
from typing import List, Literal, Optional

MAX_CONTENT_LENGTH = 80_000
MAX_MESSAGES = 50

class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., max_length=MAX_CONTENT_LENGTH)

class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    model: str
    messages: List[ChatMessage] = Field(..., max_length=MAX_MESSAGES)
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False
