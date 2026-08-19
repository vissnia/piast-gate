import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from infrastructure.detectors.validators import is_valid_iban_checksum
from domain.services.token_overlap import remove_overlapping_tokens

_WHITESPACE = re.compile(r"[ \t]")

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
                compact = _WHITESPACE.sub("", raw_val)

                checksum_input = compact if compact[:2].isalpha() else "PL" + compact
                if not is_valid_iban_checksum(checksum_input):
                    continue

                tokens.append(
                    PIIToken(
                        type=PIIType.BANK_ACCOUNT,
                        original_value=raw_val,
                        token_str="",
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return remove_overlapping_tokens(tokens)
