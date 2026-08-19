class LLMProviderError(Exception):
    """Raised for LLM provider call failures (auth/rate-limit/bad-request/...)
    and for model allow-list rejections. Carries an HTTP status code so the
    API layer can surface it without either layer depending on the other."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
