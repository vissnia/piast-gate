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
            if self.validate_pesel(val):
                tokens.append(PIIToken(
                    type=PIIType.PESEL,
                    original_value=val,
                    token_str="",
                    start=match.start(),
                    end=match.end()
                ))
        
        return tokens

    @staticmethod
    def validate_pesel(pesel: str) -> bool:
        """
        Validates the PESEL number using the checksum algorithm.

        Args:
            pesel (str): The 11-digit PESEL string to validate.

        Returns:
            bool: True if the PESEL is valid, False otherwise.
        """
        if len(pesel) != 11 or not pesel.isdigit():
            return False

        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = sum(int(pesel[i]) * weights[i] for i in range(10))
        control_digit = (10 - (checksum % 10)) % 10

        return control_digit == int(pesel[10])
