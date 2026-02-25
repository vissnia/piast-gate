from asyncio.protocols import Protocol

class LLMProvider(Protocol):
    """Interface for LLM interactions."""
    
    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Sends a conversation to the LLM and returns the response.
        
        Args:
            messages (list[dict]): The conversation messages (should be anonymized).
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum tokens to generate.
            
        Returns:
            str: The LLM's response.
        """
        pass
        