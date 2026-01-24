"""Tests for authentication module."""

import pytest
import os
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.auth import AuthManager


class TestAuthManager:
    """Test suite for AuthManager."""

    def setup_method(self):
        """Setup test fixtures."""
        os.environ['MCP_TOKEN'] = 'test-token-12345'
        self.auth_manager = AuthManager()

    def teardown_method(self):
        """Cleanup after tests."""
        if 'MCP_TOKEN' in os.environ:
            del os.environ['MCP_TOKEN']

    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token-12345"
        )
        user_id = self.auth_manager.verify_token(credentials)
        assert user_id == "authenticated_user"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="wrong-token"
        )
        with pytest.raises(HTTPException) as exc_info:
            self.auth_manager.verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_verify_token_empty(self):
        """Test token verification with empty token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""
        )
        with pytest.raises(HTTPException):
            self.auth_manager.verify_token(credentials)

    def test_verify_token_optional_none(self):
        """Test optional token verification with None."""
        result = self.auth_manager.verify_token_optional(None)
        assert result is None

    def test_verify_token_optional_valid(self):
        """Test optional token verification with valid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token-12345"
        )
        user_id = self.auth_manager.verify_token_optional(credentials)
        assert user_id == "authenticated_user"

    def test_token_generation_when_not_set(self):
        """Test token generation when MCP_TOKEN not set."""
        if 'MCP_TOKEN' in os.environ:
            del os.environ['MCP_TOKEN']

        auth_manager = AuthManager()
        assert auth_manager.valid_token is not None
        assert len(auth_manager.valid_token) > 0
