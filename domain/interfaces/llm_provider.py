from asyncio.protocols import Protocol

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
        pass
        