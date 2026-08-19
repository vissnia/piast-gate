import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from infrastructure.detectors.validators import is_valid_regon
from domain.services.token_overlap import remove_overlapping_tokens

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

        return remove_overlapping_tokens(tokens)
