import asyncio
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

    def _build_contents(self, messages: list[dict]) -> list[types.Content]:
        """
        Converts a list of chat messages into Gemini Content objects.

        Args:
            messages (list[dict]): Anonymized chat messages with 'role' and 'content'.

        Returns:
            list[types.Content]: Gemini-compatible content list with system prompt prepended.
        """
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=self._SYSTEM_PROMPT)],
            )
        ]
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])],
                )
            )
        return contents

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """
        Sends a conversation to Gemini and returns the full response.

        Args:
            messages (list[dict]): Anonymized chat messages.
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum tokens to generate.

        Returns:
            str: The LLM's complete response text.
        """
        contents = self._build_contents(messages)
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""

    async def chat_stream(self, messages, temperature=0.1, max_tokens=500):
        contents = self._build_contents(messages)

        stream = self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        loop = asyncio.get_event_loop()

        def next_chunk():
            try:
                return next(stream)
            except StopIteration:
                return None

        while True:
            chunk = await loop.run_in_executor(None, next_chunk)
            if chunk is None:
                break

            if chunk.text:
                yield chunk.text

