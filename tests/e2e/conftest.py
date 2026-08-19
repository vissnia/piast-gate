import json
import pytest
from fastapi.testclient import TestClient
from api.main import create_app
from api.config.config import settings

@pytest.fixture(scope="session", autouse=True)
def _setup_test_settings():
    """Override settings for all tests."""
    original_api_keys = settings.api_keys
    original_provider = settings.llm_provider
    
    settings.api_keys = {"test-api-key": "test-client"}
    settings.llm_provider = "mock"  
    
    yield
    
    settings.api_keys = original_api_keys
    settings.llm_provider = original_provider

@pytest.fixture(scope="session")
def app():
    """Create a FastAPI app instance for testing."""
    app = create_app()
    return app

@pytest.fixture(scope="session")
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Return headers with a valid Bearer token."""
    return {"Authorization": "Bearer test-api-key"}

@pytest.fixture
def parse_sse_chunks():
    """
    Returns a function that parses an httpx streaming response's raw lines
    as OpenAI-style SSE: yields the JSON payload of each ``data: ...`` line,
    stopping at (and not yielding) the terminal ``data: [DONE]`` sentinel.
    """
    def _parse(response):
        chunks = []
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[len("data: "):]
            if payload == "[DONE]":
                break
            chunks.append(json.loads(payload))
        return chunks
    return _parse

