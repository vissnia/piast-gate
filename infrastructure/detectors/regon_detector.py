import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from infrastructure.detectors.validators import is_valid_regon

_PATTERNS = [
    re.compile(r"\b\d{14}\b"),
    re.compile(r"\b\d{9}\b"),
]

class RegonDetector(PIIDetector):
    """Detects Polish business registry numbers (REGON, 9 or 14 digits) in text."""

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects REGON numbers in the given text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[PIIToken]: A list of detected REGON tokens.
        """
        tokens: List[PIIToken] = []

        for pattern in _PATTERNS:
            for match in pattern.finditer(text):
                val = match.group()
                if not is_valid_regon(val):
                    continue

                tokens.append(
                    PIIToken(
                        type=PIIType.REGON,
                        original_value=val,
                        token_str="",
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return self._remove_overlaps(tokens)

    def _remove_overlaps(self, tokens: List[PIIToken]) -> List[PIIToken]:
        """
        Removes overlapping tokens, keeping the longest ones.
        """
        if not tokens:
            return []

        sorted_tokens = sorted(tokens, key=lambda t: (t.start, -(t.end - t.start)))
        result = []
        last_end = -1

        for token in sorted_tokens:
            if token.start >= last_end:
                result.append(token)
                last_end = token.end

        return result
