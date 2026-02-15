from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    api_keys: List[str] = Field(default=[], description="List of valid API keys")
    rate_limit_per_minute: int = Field(default=60, description="Max requests per minute per IP")
    cors_origins: List[str] = Field(default=[], description="List of allowed CORS origins")
    cors_methods: List[str] = Field(default=["*"], description="List of allowed CORS methods")
    cors_headers: List[str] = Field(default=["*"], description="List of allowed CORS headers")
    llm_provider: str = Field(default="mock", description="LLM provider")
    gemini_api_key: str = Field(default="", description="Gemini API key")
    model_name: str = Field(default="gemini-2.5-flash", description="Model name")
    pl_ner_model_name: str = Field(default="pl_core_news_lg", description="PL NER model name")
    debug: bool = Field(default=False, description="Debug mode")
    log_file: str = Field(default="logs/app.log", description="Path to log file")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter=","

settings = Settings()
