import asyncio
import logging
import re
from typing import Callable, List, Tuple, Dict
from domain.entities.pii_token import PIIToken
from domain.interfaces.pii_detector import PIIDetector
from domain.services.token_overlap import remove_overlapping_tokens

logger = logging.getLogger(__name__)

_RESIDUAL_PLACEHOLDER_RE = re.compile(r"<[A-Z_]+\d+>")

class AnonymizerService:
    """Service responsible for replacing PII with tokens and restoring them."""

    def __init__(self, detectors: List[PIIDetector]):
        """
        Args:
            detectors (List[PIIDetector]): List of detectors to use for finding PII.
        """
        self.detectors = detectors

    def _detect_tokens(self, text: str) -> List[PIIToken]:
        """
        Runs all detectors over text and resolves overlaps.

        This is the expensive, CPU/model-bound part of anonymization and has
        no dependency on cross-message state, so it's safe to run concurrently
        for multiple texts (see :meth:`anonymize_texts_async`).
        """
        all_tokens: List[PIIToken] = []
        for detector in self.detectors:
            all_tokens.extend(detector.detect(text))

        return remove_overlapping_tokens(all_tokens)

    def _assign_tokens(self, text: str, tokens: List[PIIToken], state_type_counters: Dict[str, int] = None, state_value_to_token_str: Dict[str, str] = None) -> Tuple[str, Dict[str, PIIToken]]:
        """
        Replaces already-detected PII spans with placeholders, numbering them
        via the shared counter/value-to-token state.

        This is cheap string building with no model calls, so when anonymizing
        several texts that share numbering state, it must run sequentially in
        a fixed order (see :meth:`anonymize_texts_async`) rather than concurrently.
        """
        result_parts = []
        last_idx = 0
        mapping: Dict[str, PIIToken] = {}
        value_to_token_str: Dict[str, str] = state_value_to_token_str if state_value_to_token_str is not None else {}
        type_counters: Dict[str, int] = state_type_counters if state_type_counters is not None else {}
        for token in tokens:
            result_parts.append(text[last_idx:token.start])

            if token.original_value in value_to_token_str:
                token_str = value_to_token_str[token.original_value]
            else:
                type_name = token.type.name
                type_counters[type_name] = type_counters.get(type_name, 0) + 1
                token_str = f"<{type_name}{type_counters[type_name]}>"
                value_to_token_str[token.original_value] = token_str

            token.token_str = token_str
            mapping[token_str] = token
            result_parts.append(token_str)

            last_idx = token.end

        result_parts.append(text[last_idx:])

        return "".join(result_parts), mapping

    def anonymize(self, text: str, state_type_counters: Dict[str, int] = None, state_value_to_token_str: Dict[str, str] = None) -> Tuple[str, Dict[str, PIIToken]]:
        """
        Replaces detected PII in text with placeholders.

        Args:
            text (str): The original text.

        Returns:
            Tuple[str, Dict[str, PIIToken]]:
                - The anonymized text.
                - A mapping of token_str -> PIIToken for restoration.
        """
        tokens = self._detect_tokens(text)
        return self._assign_tokens(text, tokens, state_type_counters, state_value_to_token_str)

    def scoped(self) -> Callable[[str], str]:
        """
        Returns a closure that anonymizes text under one shared numbering
        scheme (counters + value-to-token mapping) held for its lifetime,
        so the same PII value gets the same token across repeated calls —
        e.g. paragraph by paragraph or page by page while walking a
        document. Blank/whitespace-only text passes through unchanged.
        """
        type_counters: Dict[str, int] = {}
        value_to_token_str: Dict[str, str] = {}

        def anonymize_text(text: str) -> str:
            if not text.strip():
                return text
            anonymized, _ = self.anonymize(text, type_counters, value_to_token_str)
            return anonymized

        return anonymize_text

    def deanonymize(self, text: str, mapping: Dict[str, PIIToken]) -> str:
        """
        Restores PII in the text using the provided mapping.

        Any `<TYPE#>`-shaped span left over after restoring known tokens
        (a hallucinated placeholder number, or one mangled by the LLM) is
        stripped rather than forwarded to the client: it can't be a real
        restoration, since it wasn't in the mapping, and the placeholder
        syntax itself is an internal implementation detail that shouldn't
        leak into responses either way.

        Args:
            text (str): The text containing PII tokens.
            mapping (Dict[str, PIIToken]): Token to PII mapping.

        Returns:
            str: The de-anonymized text.
        """
        if mapping:
            pattern = re.compile("|".join(map(re.escape, sorted(mapping.keys(), key=len, reverse=True))))

            def replace_match(match: re.Match) -> str:
                return mapping[match.group(0)].original_value

            text = pattern.sub(replace_match, text)

        def strip_residual(match: re.Match) -> str:
            logger.warning("Stripped unresolved placeholder tag from LLM response: %s", match.group(0))
            return ""

        return _RESIDUAL_PLACEHOLDER_RE.sub(strip_residual, text)

    def redact(self, text: str) -> Tuple[str, List[PIIToken]]:
        """
        Finds PII in text via the same detector pipeline used for
        anonymization and replaces each match with a redaction marker.

        Intended for scrubbing LLM-generated text (not user input): since
        the model is only ever shown placeholders, never real PII, any
        match found here is necessarily hallucinated (or a corrupted echo)
        rather than a legitimate restoration, and must not reach the client.

        Text inside an intact `<TYPE#>` placeholder is never scanned: a
        detector (particularly the NER one) can otherwise misread the
        placeholder's own type name as a PII-shaped span in its own right
        (e.g. the NER model reading "PERSON1" inside "<PERSON1>" as a
        name) and corrupt a legitimate token that :meth:`deanonymize`
        still needs to resolve.

        Args:
            text (str): LLM-generated text to scan.

        Returns:
            Tuple[str, List[PIIToken]]: The redacted text, and the PII
            tokens that were found and redacted (for logging; callers
            should log only ``type``/count, never ``original_value``).
        """
        protected_spans = [m.span() for m in _RESIDUAL_PLACEHOLDER_RE.finditer(text)]

        def overlaps_placeholder(token: PIIToken) -> bool:
            return any(token.start < end and token.end > start for start, end in protected_spans)

        tokens = [t for t in self._detect_tokens(text) if not overlaps_placeholder(t)]
        if not tokens:
            return text, []

        result_parts = []
        last_idx = 0
        for token in tokens:
            result_parts.append(text[last_idx:token.start])
            result_parts.append(f"[REDACTED:{token.type.name}]")
            last_idx = token.end
        result_parts.append(text[last_idx:])

        logger.warning(
            "Redacted %d hallucinated PII span(s) from LLM output: %s",
            len(tokens), [t.type.name for t in tokens],
        )

        return "".join(result_parts), tokens


    async def anonymize_async(self, text: str, state_type_counters: Dict[str, int] = None, state_value_to_token_str: Dict[str, str] = None) -> Tuple[str, Dict[str, PIIToken]]:
        """
        Async wrapper for anonymize. Offloads processing to a ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.anonymize, text, state_type_counters, state_value_to_token_str)

    async def anonymize_texts_async(self, texts: List[str]) -> Tuple[List[str], Dict[str, PIIToken]]:
        """
        Anonymizes multiple texts (e.g. all messages in a conversation) under a
        single shared numbering scheme, the same PII value gets the same token
        wherever it appears, and per-type counters keep incrementing across texts.

        Detection is the expensive, model-bound step, so it runs concurrently
        across all texts. Token assignment is cheap string work but must stay
        sequential, in input order, so numbering comes out identical to calling
        `anonymize` once per text in a loop with shared state.
        """
        if not texts:
            return [], {}

        loop = asyncio.get_running_loop()
        detected = await asyncio.gather(
            *(loop.run_in_executor(None, self._detect_tokens, text) for text in texts)
        )

        state_type_counters: Dict[str, int] = {}
        state_value_to_token_str: Dict[str, str] = {}
        global_mapping: Dict[str, PIIToken] = {}
        anonymized_texts: List[str] = []

        for text, tokens in zip(texts, detected):
            anon_text, mapping = self._assign_tokens(text, tokens, state_type_counters, state_value_to_token_str)
            global_mapping.update(mapping)
            anonymized_texts.append(anon_text)

        return anonymized_texts, global_mapping

    async def deanonymize_async(self, text: str, mapping: Dict[str, PIIToken]) -> str:
        """
        Async wrapper for deanonymize. Offloads processing to a ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.deanonymize, text, mapping)

    async def redact_async(self, text: str) -> Tuple[str, List[PIIToken]]:
        """
        Async wrapper for redact. Offloads processing to a ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.redact, text)
