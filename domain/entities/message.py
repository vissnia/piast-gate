from dataclasses import dataclass

@dataclass
class Message:
    """Represents a user message or system response."""
    text: str
    