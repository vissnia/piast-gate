import hmac
import logging
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.config.config import settings

logger = logging.getLogger(__name__)

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
        str: The name of the client the matched key belongs to.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing Authorization Token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise unauthorized

    client_name = next(
        (
            name
            for key, name in settings.api_keys.items()
            if hmac.compare_digest(credentials.credentials, key)
        ),
        None,
    )

    if client_name is None:
        raise unauthorized

    logger.info("Authenticated request from client=%s", client_name)
    return client_name
