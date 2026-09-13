from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
import phonenumbers
import re

PHONE_CANDIDATE_REGEX = re.compile(
    r'\+?\(?\d[\d\s.\-()]{6,}\d'
)
_LINEBREAK_RE = re.compile(r"\r\n|\r|\n")

class PhoneDetector(PIIDetector):
    """Detects phone numbers using phonenumbers library."""

    def detect(self, text: str) -> List[PIIToken]:
        tokens: List[PIIToken] = []

        for match in PHONE_CANDIDATE_REGEX.finditer(text):
            raw = match.group()
            cleaned = _LINEBREAK_RE.sub("", raw)

            try:
                number = phonenumbers.parse(cleaned, "PL")
                if phonenumbers.is_valid_number(number):
                    tokens.append(PIIToken(
                        type=PIIType.PHONE,
                        original_value=cleaned,
                        token_str="",
                        start=match.start(),
                        end=match.end()
                    ))
            except phonenumbers.NumberParseException:
                continue

        return tokens
