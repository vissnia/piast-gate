import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector

class BankAccountDetector(PIIDetector):
    """
    Detects bank account numbers (NRB and IBAN) in text.
    """

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects Polish NRB and international IBAN numbers in the given text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[PIIToken]: A list of detected bank account tokens.
        """
        tokens: List[PIIToken] = []

        patterns = [
            r"\b(?:\d[ \t]*){26}\b",
            r"\b[A-Z]{2}[ \t]*\d{2}[ \t]*(?:[A-Z0-9][ \t]*){11,30}\b",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                raw_val = match.group()

                tokens.append(
                    PIIToken(
                        type=PIIType.BANK_ACCOUNT,
                        original_value=raw_val,
                        token_str="",
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return self._remove_overlaps(tokens)


    def _remove_overlaps(self, tokens: List[PIIToken]) -> List[PIIToken]:
        """
        Removes overlapping tokens, keeping the longest ones.
        """
        if not tokens:
            return []

        sorted_tokens = sorted(tokens, key=lambda x: (x.start, -(x.end - x.start)))
        result = []
        last_end = -1

        for token in sorted_tokens:
            if token.start >= last_end:
                result.append(token)
                last_end = token.end
        
        return result
