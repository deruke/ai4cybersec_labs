"""
Authentication and authorization for MCP security server.
"""

import os
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .logging_config import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()


class AuthManager:
    """Manages authentication tokens and user sessions."""

    def __init__(self):
        """Initialize authentication manager."""
        # Load token from environment or generate one
        self.valid_token = os.getenv('MCP_TOKEN')

        if not self.valid_token:
            logger.warning("No MCP_TOKEN set in environment, generating random token")
            self.valid_token = secrets.token_urlsafe(32)
            logger.warning(f"Generated token: {self.valid_token}")

        logger.info("AuthManager initialized")

    def verify_token(self, credentials: HTTPAuthorizationCredentials) -> str:
        """
        Verify bearer token.

        Args:
            credentials: HTTP authorization credentials

        Returns:
            User ID/session identifier

        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials

        if not secrets.compare_digest(token, self.valid_token):
            logger.warning(f"Invalid token attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug("Token verified successfully")
        return "authenticated_user"  # Could be expanded to include user info

    def verify_token_optional(self, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
        """
        Verify bearer token if provided, otherwise return None.

        Args:
            credentials: HTTP authorization credentials (optional)

        Returns:
            User ID if authenticated, None otherwise
        """
        if credentials is None:
            return None

        return self.verify_token(credentials)


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


async def verify_authentication(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    FastAPI dependency for verifying authentication.

    Args:
        credentials: HTTP authorization credentials from request

    Returns:
        User ID/session identifier

    Raises:
        HTTPException: If authentication fails
    """
    auth_manager = get_auth_manager()
    return auth_manager.verify_token(credentials)
