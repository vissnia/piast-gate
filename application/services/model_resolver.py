from typing import Optional

from api.config.config import settings
from domain.exceptions.llm_provider_error import LLMProviderError


def resolve_model(requested: Optional[str]) -> str:
    """
    Resolves the model to call: the request's model if given, else the
    server-configured default. Rejects models outside the configured
    allow-list, when one is set.
    """
    model = requested or settings.default_model
    if settings.allowed_models and model not in settings.allowed_models:
        raise LLMProviderError(f"Model '{model}' is not permitted", status_code=400)
    return model
