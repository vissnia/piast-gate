from typing import Optional
from pydantic import BaseModel

class StreamDelta(BaseModel):
    """Incremental content in a streaming chunk."""
    role: Optional[str] = None
    content: Optional[str] = None

class StreamChoice(BaseModel):
    """A single choice entry in an SSE streaming chunk."""
    index: int = 0
    delta: StreamDelta
    finish_reason: Optional[str] = None

class StreamChatChunk(BaseModel):
    """
    OpenAI-compatible Server-Sent Event chunk for streaming chat completions.
    """
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[StreamChoice]
