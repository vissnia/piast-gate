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

        # Sort tokens by length descending to avoid partial replacements (naive approach)
        # Ideally, we should handle overlapping matches, but for MVP strict replacement is fine.
        all_tokens.sort(key=lambda t: len(t.original_value), reverse=True)

        anonymized_text = text
        mapping: Dict[str, PIIToken] = {}

        for token in all_tokens:
            # Check if this specific instance is still in the text (to avoid double replacement issues if needed)
            # For MVP regex, simple replace is okay if patterns are distinct.
            
            # Generate a consistent token string if not already provided by detector
            # logic: <PII:TYPE:VALUE_HASH> or just a unique ID for this request?
            # The prompt says: <PII:TYPE:ID>
            # We'll generate a unique ID for this specific occurrence or value.
            # To preserve consistent mapping for the same value in one request:
            
            if token.original_value not in [t.original_value for t in mapping.values()]:
                # New unique value found
                unique_id = str(uuid.uuid4())[:8]
                token_str = f"<PII:{token.type.name}:{unique_id}>"
                token.token_str = token_str # update token with generated string
                mapping[token_str] = token
            else:
                # Existing value, reuse the token string
                existing_token = next(t for t in mapping.values() if t.original_value == token.original_value)
                token.token_str = existing_token.token_str

            # Replace in text
            # Note: This simple replace might replace partial matches if not careful.
            # Ideally we replace by index, but string immutability makes that tricky without reconstruction.
            # For MVP, string.replace is acceptable if assumes unique context or comprehensive regex.
            anonymized_text = anonymized_text.replace(token.original_value, token.token_str)

        return anonymized_text, mapping

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
