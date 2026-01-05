from dataclasses import dataclass

@dataclass
class PIIToken:
    """Represents a detected PII entity and its replacement token."""
    type: PIIType
    original_value: str
    token_str: str
    start: int
    end: int
    