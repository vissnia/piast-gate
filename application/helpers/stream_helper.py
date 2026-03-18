from application.dtos.chat_request import ChatRequest
from application.dtos.stream_chat_chunk import StreamChatChunk, StreamMessage
from datetime import datetime, timezone

def build_chunk(request: ChatRequest, content: str, thinking: str, done: bool) -> StreamChatChunk:
    return StreamChatChunk(
        model=request.model,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z",
        message=StreamMessage(role="assistant", content=content, thinking=thinking),
        done=done
    )