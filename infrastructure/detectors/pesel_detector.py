import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector

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

        pattern = r'\b\d{11}\b'
        matches = re.finditer(pattern, text)
        for match in matches:
            val = match.group()
            tokens.append(PIIToken(
                    type=PIIType.PESEL,
                    original_value=val,
                    token_str="",
                    start=match.start(),
                    end=match.end()
                ))
        
        return tokens
