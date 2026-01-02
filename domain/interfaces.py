from typing import List, Protocol
from domain.entities import PIIToken

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

class LLMProvider(Protocol):
    """Interface for LLM interactions."""
    
    async def chat(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns the response.
        
        Args:
            prompt (str): The prompt to send (should be anonymized).
            
        Returns:
            str: The LLM's response.
        """
        ...
