from google import genai
from google.genai import types
from domain.interfaces.llm_provider import LLMProvider

class GeminiLLM(LLMProvider):
    """Google Gemini LLM implementation."""

    _SYSTEM_PROMPT = """
IMPORTANT: You are part of a PII scrubbing system.
User prompts may contain anonymized tokens like <PII_TYPE_AND_ID_NUMBER>.
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

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        contents = []

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=self._SYSTEM_PROMPT)],
            )
        )

        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"

            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])],
                )
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        return response.text or ""
