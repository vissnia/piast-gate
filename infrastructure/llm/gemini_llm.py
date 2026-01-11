from google import genai
from domain.interfaces.llm_provider import LLMProvider

class GeminiLLM(LLMProvider):
    """Google Gemini LLM implementation."""

    _SYSTEM_PROMPT = """
IMPORTANT: You are part of a PII scrubbing system.
User prompts may contain anonymized tokens like <PII:TYPE:ID>.
YOU MUST PRESERVE THESE TOKENS EXACTLY IN YOUR RESPONSE.
DO NOT modify, rename, or obfuscate them.
"""

    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("Gemini API key is required")
            
        if not model_name:
            raise ValueError("Gemini model name is required")
        
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    async def chat(self, prompt: str) -> str:
        try:
            full_prompt = f"{self._SYSTEM_PROMPT}\n\nUser: {prompt}"
            response = self.client.models.generate_content(contents=full_prompt, model=self.model)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")
