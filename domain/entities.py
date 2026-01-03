from dataclasses import dataclass
from enum import Enum, auto

class PIIType(Enum):
    """Enumeration of supported PII types."""
    EMAIL = auto()
    PHONE = auto()
    PESEL = auto()

@dataclass
class PIIToken:
    """Represents a detected PII entity and its replacement token."""
    type: PIIType
    original_value: str
    token_str: str
    start: int
    end: int

@dataclass
class Message:
    """Represents a user message or system response."""
    text: str
