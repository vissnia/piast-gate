from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from application.dtos.chat_response import ChatUsage

class ChatChunkDelta(BaseModel):
    """
    OpenAI ``chat.completion.chunk``-style delta. Only the fields actually
    present on a given chunk are set; the rest stay ``None`` and are dropped
    at serialisation time (see ``exclude_none`` in ``_stream_generator``).
    ``thinking`` is a non-standard extension carrying reasoning-model
    "thinking" text out of band from ``content`` — off-the-shelf OpenAI
    clients that don't recognise it simply ignore the extra field.
    """
    role: Optional[str] = None
    content: Optional[str] = None
    thinking: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatChunkChoice(BaseModel):
    index: int = 0
    delta: ChatChunkDelta
    finish_reason: Optional[str] = None

class StreamChatChunk(BaseModel):
    """
    OpenAI ``chat.completion.chunk``-compatible streaming chunk. ``usage``
    is only set on a final, content-less chunk with empty ``choices`` once
    the provider has reported it (mirrors OpenAI/litellm's
    ``stream_options={"include_usage": True}`` behaviour).
    """
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatChunkChoice] = []
    usage: Optional[ChatUsage] = None
