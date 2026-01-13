import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector

class EmailDetector(PIIDetector):
    """Detects email addresses using regular expressions."""

    def detect(self, text: str) -> List[PIIToken]:
        tokens: List[PIIToken] = []

        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(pattern, text)
        for match in matches:
            val = match.group()
            tokens.append(PIIToken(
                type=PIIType.EMAIL,
                original_value=val,
                token_str="",
                start=match.start(),
                end=match.end()
            ))
        
        return tokens
