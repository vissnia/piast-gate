import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from domain.services.token_overlap import remove_overlapping_tokens

_MONTHS = (
    r"stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|"
    r"sierpnia|września|października|listopada|grudnia"
)

_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b"),
    re.compile(rf"\b\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b(?:\s+roku\b)?"),
]

class DateDetector(PIIDetector):
    """Detects dates (ISO, numeric and Polish long-form) in text."""

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects dates in the given text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[PIIToken]: A list of detected date tokens.
        """
        tokens: List[PIIToken] = []

        for pattern in _PATTERNS:
            for match in pattern.finditer(text):
                tokens.append(
                    PIIToken(
                        type=PIIType.DATE,
                        original_value=match.group(),
                        token_str="",
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return remove_overlapping_tokens(tokens)
