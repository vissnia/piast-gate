from enum import Enum, auto
from typing import AsyncIterator, Dict
from domain.entities.pii_token import PIIToken

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
                        pii = self._mapping.get(self._buffer)
                        if pii:
                            output.append(pii.original_value)
                        else:
                            output.append(self._buffer)
                        
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
