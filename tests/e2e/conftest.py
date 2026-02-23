import pytest
from fastapi.testclient import TestClient
from api.main import create_app
from api.config.config import settings

@pytest.fixture(scope="session", autouse=True)
def _setup_test_settings():
    """Override settings for all tests."""
    original_api_keys = settings.api_keys
    original_provider = settings.llm_provider
    
    settings.api_keys = ["test-api-key"]
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
    """Return headers with a valid API key."""
    return {"X-API-KEY": "test-api-key"}
