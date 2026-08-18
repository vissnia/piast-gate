from dataclasses import dataclass


@dataclass
class Usage:
    """Token usage for a single LLM call, as reported by the provider."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
