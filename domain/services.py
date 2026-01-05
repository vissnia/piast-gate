import logging
import uuid
from typing import List, Tuple, Dict
from domain.entities import PIIToken, PIIType
from domain.interfaces import PIIDetector

logger = logging.getLogger(__name__)

class AnonymizerService:
    """Service responsible for replacing PII with tokens and restoring them."""

    def __init__(self, detectors: List[PIIDetector]):
        """
        Args:
            detectors (List[PIIDetector]): List of detectors to use for finding PII.
        """
        self.detectors = detectors

    def anonymize(self, text: str) -> Tuple[str, Dict[str, PIIToken]]:
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

        # Sort by start position (asc) and length (desc) to prioritize longer matches at same position
        all_tokens.sort(key=lambda t: (t.start, -len(t.original_value)))

        non_overlapping_tokens: List[PIIToken] = []
        last_end = 0

        for token in all_tokens:
            if token.start >= last_end:
                non_overlapping_tokens.append(token)
                last_end = token.end
        
        # Build result and generate tokens
        result_parts = []
        last_idx = 0
        mapping: Dict[str, PIIToken] = {}
        # Keep track of value -> token_str for consistency within this request
        value_to_token_str: Dict[str, str] = {}

        for token in non_overlapping_tokens:
            # Append text before this token
            result_parts.append(text[last_idx:token.start])

            # consistency check
            if token.original_value in value_to_token_str:
                token_str = value_to_token_str[token.original_value]
            else:
                unique_id = str(uuid.uuid4())[:8]
                token_str = f"<PII:{token.type.name}:{unique_id}>"
                value_to_token_str[token.original_value] = token_str
            
            token.token_str = token_str
            mapping[token_str] = token
            result_parts.append(token_str)
            
            last_idx = token.end

        # Append remaining text
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
        deanonymized_text = text
        for token_str, token in mapping.items():
            deanonymized_text = deanonymized_text.replace(token_str, token.original_value)
        
        return deanonymized_text
