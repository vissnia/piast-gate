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
        
        result_parts = []
        last_idx = 0
        mapping: Dict[str, PIIToken] = {}
        value_to_token_str: Dict[str, str] = state_value_to_token_str if state_value_to_token_str is not None else {}
        type_counters: Dict[str, int] = state_type_counters if state_type_counters is not None else {}
        for token in non_overlapping_tokens:
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

    async def deanonymize_async(self, text: str, mapping: Dict[str, PIIToken]) -> str:
        """
        Async wrapper for deanonymize. Offloads processing to a ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.deanonymize, text, mapping)
