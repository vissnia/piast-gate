from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Literal, Optional, Union

MAX_CONTENT_LENGTH = 80_000
MAX_MESSAGES = 50

ContentPart = Dict[str, Any]

class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[Union[str, List[ContentPart]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    @field_validator("content")
    @classmethod
    def _enforce_max_length(cls, content):
        if content is None:
            return content
        if isinstance(content, str):
            length = len(content)
        else:
            length = sum(len(part.get("text", "")) for part in content if part.get("type") == "text")
        if length > MAX_CONTENT_LENGTH:
            raise ValueError(f"content exceeds max length of {MAX_CONTENT_LENGTH} characters")
        return content

class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    model: Optional[str] = None
    messages: List[ChatMessage] = Field(..., max_length=MAX_MESSAGES)
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False
    top_p: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    seed: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
