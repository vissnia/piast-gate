import re
from typing import List
from domain.entities import PIIToken, PIIType
from domain.interfaces import PIIDetector

class RegexPIIDetector:
    """Detects PII using regular expressions."""

    # Simplified patterns for MVP
    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'(?:\+48\s?)?[1-9]\d{2}[-\s]?\d{3}[-\s]?\d{3}\b',
        PIIType.PESEL: r'\b\d{11}\b', # Simple 11 digit check for PESEL to change later
    }

    def detect(self, text: str) -> List[PIIToken]:
        tokens: List[PIIToken] = []

        for pii_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                val = match.group()
                tokens.append(PIIToken(
                    type=pii_type,
                    original_value=val,
                    token_str="" # Placeholder, set by service
                ))
        
        return tokens
