from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Dict, List, Optional

class Settings(BaseSettings):
    api_keys: Dict[str, str] = Field(default_factory=dict, description="Map of valid API key -> client name")
    rate_limit_per_minute: int = Field(default=60, description="Max requests per minute per IP")
    cors_origins: List[str] = Field(default_factory=list, description="List of allowed CORS origins")
    cors_methods: List[str] = Field(default_factory=lambda: ["*"], description="List of allowed CORS methods")
    cors_headers: List[str] = Field(default_factory=lambda: ["*"], description="List of allowed CORS headers")
    allow_credentials: bool = Field(default=False, description="Allow credentials")
    llm_provider: str = Field(default="mock", description="LLM provider: mock or litellm")
    default_model: str = Field(default="gemini/gemini-2.5-flash", description="Default model when a request doesn't specify one, in litellm's '<provider>/<model>' form")
    allowed_models: List[str] = Field(default_factory=list, description="If non-empty, only these exact model strings may be requested per-call; empty = any model litellm supports is allowed")
    litellm_proxy_api_base: Optional[str] = Field(default=None, description="Base URL of an externally-hosted LiteLLM Proxy. Only used for models requested with the 'litellm_proxy/' prefix — other model prefixes (gemini/, openai/, ...) always call the provider directly via the litellm library, regardless of this setting")
    litellm_proxy_api_key: Optional[str] = Field(default=None, description="Virtual API key issued by the external LiteLLM Proxy (not a real provider key). Used only for 'litellm_proxy/' models")
    llm_num_retries: int = Field(default=2, description="Number of times litellm retries a request on transient provider errors (timeouts, rate limits, connection errors) before surfacing a failure")
    pl_ner_model_name: str = Field(default="radlab/pii-pl-v1.0", description="PL NER model name")
    pl_ner_chunk_tokens: int = Field(default=384, description="Max tokens per NER inference window (smaller = cheaper attention per chunk)")
    pl_ner_chunk_stride: int = Field(default=64, description="Token overlap between NER inference windows, to avoid splitting entities at chunk boundaries")
    debug: bool = Field(default=False, description="Debug mode")
    log_file: str = Field(default="logs/app.log", description="Path to log file")
    max_upload_size: int = Field(default=10 * 1024 * 1024, description="Max upload size in bytes (default 10MB)")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter=",",
        extra="ignore",
    )


settings = Settings()
