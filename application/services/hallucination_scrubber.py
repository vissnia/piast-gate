import re
from typing import AsyncIterator
from domain.services.anonymizer_service import AnonymizerService

_WORD_RE = re.compile(r"\S+\s+")

class HallucinationScrubber:
    """
    Buffers a streamed LLM response by whitespace-delimited word and scrubs
    any word that is itself PII recognised by the fast, checksum-validated
    detectors (email/phone/PESEL/NIP/REGON/bank account).

    The LLM only ever sees placeholders, never real PII, so a PII-shaped
    word in its own output is hallucinated (or a corrupted echo), not a
    legitimate restoration — restoration happens later, downstream, via
    :class:`~application.services.stream_deanonymizer.StreamDeanonymizer`,
    against `<TYPE#>`-shaped tokens that don't look like PII data and so
    are never touched here.

    Deliberately scoped to fast, non-NER detectors: running the PL NER
    model per streamed word would add prohibitive latency. Multi-word
    hallucinated PII (e.g. names) is not caught in streaming mode — only
    the non-streaming path, which scans the complete response at once via
    :meth:`AnonymizerService.redact`, catches those.
    """

    def __init__(self, guard: AnonymizerService) -> None:
        """
        Args:
            guard (AnonymizerService): scoped to fast, non-NER detectors only.
        """
        self._guard = guard
        self._buffer = ""

    async def process(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """
        Consumes an upstream text stream and yields it back with any
        hallucinated PII words redacted.

        Args:
            stream (AsyncIterator[str]): Raw text chunks to scan.

        Yields:
            str: Text safe to forward downstream.
        """
        async for chunk in stream:
            if not chunk:
                continue

            self._buffer += chunk
            output = []
            last_end = 0
            for match in _WORD_RE.finditer(self._buffer):
                word = match.group()
                scrubbed, _ = self._guard.redact(word)
                output.append(scrubbed)
                last_end = match.end()

            self._buffer = self._buffer[last_end:]
            if output:
                yield "".join(output)

        if self._buffer:
            scrubbed, _ = self._guard.redact(self._buffer)
            yield scrubbed
            self._buffer = ""
