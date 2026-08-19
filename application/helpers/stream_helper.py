from typing import Any, Dict, List, Optional
from application.dtos.stream_chat_chunk import ChatChunkChoice, ChatChunkDelta, StreamChatChunk

def build_chunk(
    id: str,
    created: int,
    model: str,
    role: Optional[str] = None,
    content: Optional[str] = None,
    thinking: Optional[str] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    finish_reason: Optional[str] = None,
) -> StreamChatChunk:
    return StreamChatChunk(
        id=id,
        created=created,
        model=model,
        choices=[
            ChatChunkChoice(
                delta=ChatChunkDelta(role=role, content=content, thinking=thinking, tool_calls=tool_calls),
                finish_reason=finish_reason,
            )
        ],
    )
