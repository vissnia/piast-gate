import re
from typing import AsyncIterator, Dict
from domain.entities.pii_token import PIIToken

class StreamDeanonymizer:
    """
    Safely de-anonymizes a streaming LLM response.
    """

    _PLACEHOLDER_RE = re.compile(r"<[A-Z_]+\d+>")

    def __init__(self, mapping: Dict[str, PIIToken]) -> None:
        """
        Args:
            mapping (Dict[str, PIIToken]): token_str -> PIIToken from anonymization phase.
        """
        self._mapping = mapping
        self._buffer: str = ""

    def _replace_complete_placeholders(self, text: str) -> str:
        """
        Replaces every complete PII placeholder found in text with its original value.

        Args:
            text (str): Text that may contain complete placeholders.

        Returns:
            str: Text with all known placeholders replaced by original values.
        """
        if not self._mapping:
            return text

        def _sub(match: re.Match) -> str:
            token = match.group(0)
            pii = self._mapping.get(token)
            return pii.original_value if pii else token

        return self._PLACEHOLDER_RE.sub(_sub, text)

    def _flush_safe(self, force: bool = False) -> str:
        """
        Emits as much of the internal buffer as can be safely forwarded.

        Args:
            force (bool): Flush the entire buffer unconditionally.

        Returns:
            str: The safe portion with placeholders replaced.
        """
        if force:
            output = self._replace_complete_placeholders(self._buffer)
            self._buffer = ""
            return output

        output_parts = []

        while self._buffer:
            lt_index = self._buffer.find("<")

            if lt_index == -1:
                output_parts.append(self._replace_complete_placeholders(self._buffer))
                self._buffer = ""
                break
            if lt_index > 0:
                safe_part = self._buffer[:lt_index]
                output_parts.append(self._replace_complete_placeholders(safe_part))
                self._buffer = self._buffer[lt_index:]

            gt_index = self._buffer.find(">")
            if gt_index == -1:
                break

            complete_token = self._buffer[: gt_index + 1]
            replaced = self._replace_complete_placeholders(complete_token)
            output_parts.append(replaced)
            self._buffer = self._buffer[gt_index + 1 :]

        return "".join(output_parts)

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
            
            self._buffer += chunk
            safe_output = self._flush_safe(force=False)
            if safe_output:
                yield safe_output

        if self._buffer:
            final_output = self._flush_safe(force=True)
            if final_output:
                yield final_output
