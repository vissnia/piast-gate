import re
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from domain.services.token_overlap import remove_overlapping_tokens

_OCR_BREAK_RE = re.compile(r"-\r?\n")

_LOCAL = r"[A-Za-z0-9._%+-]+(?:-\r?\n[A-Za-z0-9._%+-]+)*"
_QUOTED_LOCAL = r'"[^"\r\n]+"'
_DOMAIN = r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
_IP_DOMAIN = r"\[\d{1,3}(?:\.\d{1,3}){3}\]"

_KNOWN_TLDS = "pl|com|org|net|io|eu|de|uk|gov|edu|info|biz|co"

_MASKED_AT = r"\s*[\(\[]\s*at\s*[\)\]]\s*"
_MASKED_DOT = r"\s*(?:\.|[\(\[]\s*dot\s*[\)\]])\s*"

_PATTERNS = [
    re.compile(rf"{_QUOTED_LOCAL}@{_DOMAIN}\b"),
    re.compile(rf"\b{_LOCAL}@{_IP_DOMAIN}"),
    re.compile(rf"\b{_LOCAL}@[A-Za-z0-9.-]+\.(?:{_KNOWN_TLDS})", re.IGNORECASE),
    re.compile(rf"\b{_LOCAL}@{_DOMAIN}\b"),
    re.compile(rf"\b[A-Za-z0-9._%+-]+{_MASKED_AT}[A-Za-z0-9-]+(?:{_MASKED_DOT}[A-Za-z0-9-]+)+\b", re.IGNORECASE),
]

class EmailDetector(PIIDetector):
    """Detects email addresses using regular expressions."""

    def detect(self, text: str) -> List[PIIToken]:
        tokens: List[PIIToken] = []

        for pattern in _PATTERNS:
            for match in pattern.finditer(text):
                raw_val = match.group()
                tokens.append(PIIToken(
                    type=PIIType.EMAIL,
                    original_value=_OCR_BREAK_RE.sub("-", raw_val),
                    token_str="",
                    start=match.start(),
                    end=match.end()
                ))

        return remove_overlapping_tokens(tokens)
