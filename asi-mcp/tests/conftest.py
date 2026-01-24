"""Pytest configuration and fixtures."""

import pytest
import os


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ['MCP_TOKEN'] = 'test-token-12345'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['AUTHORIZED_NETWORKS'] = '10.0.0.0/8,172.16.0.0/12,192.168.0.0/16'
    os.environ['BLACKLISTED_NETWORKS'] = '127.0.0.0/8'

    yield

    # Cleanup
    for key in ['MCP_TOKEN', 'LOG_LEVEL', 'AUTHORIZED_NETWORKS', 'BLACKLISTED_NETWORKS']:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_validator():
    """Fixture for mocked SafetyValidator."""
    from unittest.mock import Mock
    validator = Mock()
    validator.validate_target.return_value = True
    validator.validate_ip.return_value = True
    validator.validate_hostname.return_value = True
    return validator
