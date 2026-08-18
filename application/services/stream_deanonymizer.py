import logging
import re
from enum import Enum, auto
from typing import AsyncIterator, Dict
from domain.entities.pii_token import PIIToken

logger = logging.getLogger(__name__)

_PLACEHOLDER_SHAPE_RE = re.compile(r"^<([A-Z_]+)\d+>$")

class State(Enum):
    NORMAL = auto()
    IN_TAG = auto()

class StreamDeanonymizer:
    """
    Safely de-anonymizes a streaming LLM response using a state machine.
    """

    def __init__(self, mapping: Dict[str, PIIToken]) -> None:
        """
        Args:
            mapping (Dict[str, PIIToken]): token_str -> PIIToken from anonymization phase.
        """
        self._mapping = mapping
        self._state = State.NORMAL
        self._buffer: str = ""

    async def process(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """
        Consumes an upstream LLM chunk stream and yields de-anonymized text.

        Args:
            stream (AsyncIterator[str]): Raw text chunks from the LLM provider.

        Yields:
            str: De-anonymized text safe to forward to the client.
        """
        async for chunk in stream:
            if not chunk:
                continue
            
            output = []
            for char in chunk:
                if self._state == State.NORMAL:
                    if char == '<':
                        self._state = State.IN_TAG
                        self._buffer = char
                    else:
                        output.append(char)
                elif self._state == State.IN_TAG:
                    self._buffer += char
                    if char == '>':
                        output.append(self._resolve_tag(self._buffer))
                        self._buffer = ""
                        self._state = State.NORMAL
                    elif char == '<':
                        output.append(self._buffer[:-1])
                        self._buffer = char
            
            if output:
                yield "".join(output)

        if self._buffer:
            yield self._buffer
            self._buffer = ""
            self._state = State.NORMAL

    def _resolve_tag(self, tag: str) -> str:
        """
        Resolves a complete `<...>` tag captured by the state machine.

        A tag matching a known placeholder is restored to its original
        value. A tag that merely *looks* like our placeholder format
        (`<TYPE#>`) but isn't in the mapping is a hallucinated or
        corrupted tag — it can't be forwarded as-is (that would leak the
        internal placeholder syntax, or a malformed near-miss of it), so
        it's redacted instead. Anything else (e.g. genuine angle-bracket
        text like "<3" or "<b>") is passed through unchanged.
        """
        pii = self._mapping.get(tag)
        if pii:
            return pii.original_value

        shape_match = _PLACEHOLDER_SHAPE_RE.match(tag)
        if shape_match:
            logger.warning("Dropped unresolved placeholder tag from streamed response: %s", tag)
            return f"[REDACTED:{shape_match.group(1)}]"

        return tag
