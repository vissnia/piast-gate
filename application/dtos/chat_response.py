from pydantic import BaseModel
from typing import List, Literal

class ChatChoiceMessage(BaseModel):
    role: Literal["assistant"]
    content: str

class ChatChoice(BaseModel):
    index: int
    message: ChatChoiceMessage
    finish_reason: str = "stop"

class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: ChatUsage