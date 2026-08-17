import asyncio
import logging
import re
from typing import List, Tuple, Dict
from domain.entities.pii_token import PIIToken
from domain.interfaces.pii_detector import PIIDetector

logger = logging.getLogger(__name__)

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

        all_tokens.sort(key=lambda t: (t.start, -len(t.original_value)))

        non_overlapping_tokens: List[PIIToken] = []
        last_end = 0

        for token in all_tokens:
            if token.start >= last_end:
                non_overlapping_tokens.append(token)
                last_end = token.end

        return non_overlapping_tokens

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

    def deanonymize(self, text: str, mapping: Dict[str, PIIToken]) -> str:
        """
        Restores PII in the text using the provided mapping.

        Args:
            text (str): The text containing PII tokens.
            mapping (Dict[str, PIIToken]): Token to PII mapping.

        Returns:
            str: The de-anonymized text.
        """
        if not mapping:
            return text

        pattern = re.compile("|".join(map(re.escape, sorted(mapping.keys(), key=len, reverse=True))))
        
        def replace_match(match: re.Match) -> str:
            return mapping[match.group(0)].original_value
            
        return pattern.sub(replace_match, text)


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
