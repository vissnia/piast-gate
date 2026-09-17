import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from domain.services.token_overlap import remove_overlapping_tokens

_SEPARATOR = r"[ \t\r\n\-]"
_SEPARATOR_RE = re.compile(_SEPARATOR)
_LINEBREAK_RE = re.compile(r"\r\n|\r|\n")

_NRB_PATTERN = re.compile(rf"(?<![A-Za-z0-9])\d(?:{_SEPARATOR}*\d){{25}}(?!\d)")
_IBAN_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9])[A-Za-z]{{2}}\d{{2}}(?:{_SEPARATOR}*\d){{11,30}}(?![A-Za-z0-9])"
)


def _account_body(compact: str) -> str:
    prefix_len = 4 if compact[:2].isalpha() else 2
    return compact[prefix_len:]


def _is_placeholder(body: str) -> bool:
    return len(set(body)) == 1


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

        for pattern in (_NRB_PATTERN, _IBAN_PATTERN):
            for match in pattern.finditer(text):
                raw_val = match.group()
                compact = _SEPARATOR_RE.sub("", raw_val)

                if _is_placeholder(_account_body(compact)):
                    continue

                tokens.append(
                    PIIToken(
                        type=PIIType.BANK_ACCOUNT,
                        original_value=_LINEBREAK_RE.sub("", raw_val),
                        token_str="",
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return remove_overlapping_tokens(tokens)
