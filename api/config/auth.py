from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.config.config import settings

security = HTTPBearer(auto_error=False)

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Verify the Bearer token against the configured API keys.

    Args:
        credentials (HTTPAuthorizationCredentials): The credentials extracted
            from the Authorization header.

    Returns:
        str: The valid token if authorized.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    if not credentials or credentials.credentials not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

