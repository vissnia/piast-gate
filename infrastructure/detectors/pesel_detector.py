import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from infrastructure.detectors.validators import is_valid_pesel
from domain.services.token_overlap import remove_overlapping_tokens

_SEPARATOR = r"[ \t\r\n.\-]"
_SEPARATOR_RE = re.compile(_SEPARATOR)
_LINEBREAK_RE = re.compile(r"\r\n|\r|\n")

_PATTERN = re.compile(rf"(?<!\d)\d(?:{_SEPARATOR}*\d){{10}}(?!\d)")

class PeselDetector(PIIDetector):
    """Detects Pesel in text."""

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PESEL numbers in the given text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[PIIToken]: A list of detected PESEL tokens.
        """
        tokens: List[PIIToken] = []

        for match in _PATTERN.finditer(text):
            raw_val = match.group()
            digits = _SEPARATOR_RE.sub("", raw_val)
            if not is_valid_pesel(digits):
                continue
            tokens.append(PIIToken(
                    type=PIIType.PESEL,
                    original_value=_LINEBREAK_RE.sub("", raw_val),
                    token_str="",
                    start=match.start(),
                    end=match.end()
                ))

        return remove_overlapping_tokens(tokens)
