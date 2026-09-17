import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from infrastructure.detectors.validators import is_valid_regon
from domain.services.token_overlap import remove_overlapping_tokens

_SEPARATOR = r"[ \t\r\n\-]"
_SEPARATOR_RE = re.compile(_SEPARATOR)
_LINEBREAK_RE = re.compile(r"\r\n|\r|\n")

_PATTERNS = [
    re.compile(rf"(?<!\d)\d(?:{_SEPARATOR}*\d){{13}}(?!\d)"),
    re.compile(rf"(?<!\d)\d(?:{_SEPARATOR}*\d){{8}}(?!\d)"),
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
                raw_val = match.group()
                digits = _SEPARATOR_RE.sub("", raw_val)
                if not is_valid_regon(digits):
                    continue

                tokens.append(
                    PIIToken(
                        type=PIIType.REGON,
                        original_value=_LINEBREAK_RE.sub("", raw_val),
                        token_str="",
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return remove_overlapping_tokens(tokens)
