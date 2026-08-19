from dataclasses import dataclass
from typing import List, Optional

from domain.entities.usage import Usage


@dataclass
class ToolCall:
    """A single tool/function call requested by the model. Arguments are the
    raw JSON string from the provider — unparsed and not scanned for PII."""
    id: str
    name: str
    arguments: str


@dataclass
class LLMResponse:
    """A complete, non-streamed response from an LLM provider."""
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: str = "stop"
    usage: Optional[Usage] = None
