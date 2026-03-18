from pydantic import BaseModel

class StreamMessage(BaseModel):
    """
    Message structure for the streaming chunk.
    Compatible with Ollama-style stream format.
    """
    role: str = "assistant"
    content: str = ""
    thinking: str = ""

class StreamChatChunk(BaseModel):
    """
    Ollama-style streaming chat completion chunk.
    """
    model: str
    created_at: str
    message: StreamMessage
    done: bool = False
