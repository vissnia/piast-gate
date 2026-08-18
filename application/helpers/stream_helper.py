from typing import Any, Dict, List, Optional
from application.dtos.chat_request import ChatRequest
from application.dtos.chat_response import ChatUsage
from application.dtos.stream_chat_chunk import StreamChatChunk, StreamMessage
from datetime import datetime, timezone

def build_chunk(
    request: ChatRequest,
    content: str,
    thinking: str,
    done: bool,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    model: Optional[str] = None,
    usage: Optional[ChatUsage] = None,
) -> StreamChatChunk:
    return StreamChatChunk(
        model=model or request.model or "",
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z",
        message=StreamMessage(role="assistant", content=content, thinking=thinking, tool_calls=tool_calls),
        done=done,
        usage=usage,
    )