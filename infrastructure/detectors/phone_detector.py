import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector

class PhoneDetector(PIIDetector):
    """Detects phone numbers using regular expressions."""

    def detect(self, text: str) -> List[PIIToken]:
        tokens: List[PIIToken] = []
        pattern = r'\b(?:\+48\s?)?[1-9]\d{2}[-\s]?\d{3}[-\s]?\d{3,4}\b'
        matches = re.finditer(pattern, text)
        for match in matches:
            val = match.group()
            tokens.append(PIIToken(
                    type=PIIType.PHONE,
                    original_value=val,
                    token_str="",
                    start=match.start(),
                    end=match.end()
                ))
        
        return tokens
