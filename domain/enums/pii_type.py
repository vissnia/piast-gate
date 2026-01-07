from enum import Enum, auto

class PIIType(Enum):
    """Enumeration of supported PII types."""
    EMAIL = auto()
    PHONE = auto()
    PESEL = auto()
    PERSON = auto()
    LOCATION = auto()
    ORGANIZATION = auto()
    