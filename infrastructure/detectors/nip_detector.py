import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from infrastructure.detectors.validators import is_valid_nip
from domain.services.token_overlap import remove_overlapping_tokens

_SEPARATOR = r"[ \t\r\n\-]"
_SEPARATOR_RE = re.compile(_SEPARATOR)
_LINEBREAK_RE = re.compile(r"\r\n|\r|\n")

_DOMESTIC_PATTERN = re.compile(rf"(?<!\d)\d(?:{_SEPARATOR}*\d){{9}}(?!\d)(?!-?[A-Za-z])")

_FOREIGN_PATTERN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{8,12}(?!\d)")

class NipDetector(PIIDetector):
    """Detects Polish tax identification numbers (NIP) in text."""

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects NIP numbers (plain, separated, glued to a label, or with an
        EU-style two-letter country prefix) in the given text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[PIIToken]: A list of detected NIP tokens.
        """
        tokens: List[PIIToken] = []

        for match in _DOMESTIC_PATTERN.finditer(text):
            raw_val = match.group()
            digits = _SEPARATOR_RE.sub("", raw_val)
            if not is_valid_nip(digits):
                continue

            tokens.append(
                PIIToken(
                    type=PIIType.NIP,
                    original_value=_LINEBREAK_RE.sub("", raw_val),
                    token_str="",
                    start=match.start(),
                    end=match.end(),
                )
            )

        for match in _FOREIGN_PATTERN.finditer(text):
            raw_val = match.group()
            prefix, digits = raw_val[:2], raw_val[2:]

            if prefix == "PL" and (len(digits) != 10 or not is_valid_nip(digits)):
                continue

            tokens.append(
                PIIToken(
                    type=PIIType.NIP,
                    original_value=raw_val,
                    token_str="",
                    start=match.start(),
                    end=match.end(),
                )
            )

        return remove_overlapping_tokens(tokens)
