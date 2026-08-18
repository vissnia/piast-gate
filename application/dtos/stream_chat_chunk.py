from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from application.dtos.chat_response import ChatUsage

class StreamMessage(BaseModel):
    """
    Message structure for the streaming chunk.
    Compatible with Ollama-style stream format.
    """
    role: str = "assistant"
    content: str = ""
    thinking: str = ""
    tool_calls: Optional[List[Dict[str, Any]]] = None

class StreamChatChunk(BaseModel):
    """
    Ollama-style streaming chat completion chunk. ``usage`` is only set on
    the final (``done=True``) chunk, once the provider has reported it.
    """
    model: str
    created_at: str
    message: StreamMessage
    done: bool = False
    usage: Optional[ChatUsage] = None
