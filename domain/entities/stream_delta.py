from dataclasses import dataclass
from typing import List, Optional

from domain.entities.usage import Usage


@dataclass
class ToolCallDelta:
    """A fragment of a streamed tool call. ``id``/``name`` are only set on
    the first delta for a given tool call; subsequent fragments are keyed by
    ``index`` and carry a partial-JSON ``arguments_fragment`` to accumulate."""
    index: int
    id: Optional[str]
    name: Optional[str]
    arguments_fragment: str


@dataclass
class StreamDelta:
    """A single chunk from a streamed LLM response. ``usage`` is only ever
    set on a final, content-less delta (mirrors OpenAI/litellm's
    stream_options={"include_usage": True} behavior: one extra chunk with
    empty choices, carrying the whole request's token usage)."""
    content: str = ""
    tool_call_deltas: Optional[List[ToolCallDelta]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Usage] = None
