from typing import List, Protocol
from domain.entities.pii_token import PIIToken

class PIIDetector(Protocol):
    """Interface for PII detection strategies."""
    
    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PII in the given text.
        
        Args:
            text (str): Input text to analyze.
            
        Returns:
            List[PIIToken]: List of detected PII tokens with their positions/values.
        """
        ...