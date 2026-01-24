"""Tests for safety validation module."""

import pytest
from src.safety import SafetyValidator, UnauthorizedTargetError, InvalidTargetError


class TestSafetyValidator:
    """Test suite for SafetyValidator."""

    def setup_method(self):
        """Setup test fixtures."""
        self.validator = SafetyValidator()

    def test_validate_ip_authorized(self):
        """Test validation of authorized IP addresses."""
        # Should pass for private networks
        assert self.validator.validate_ip("10.0.0.1") is True
        assert self.validator.validate_ip("172.16.0.1") is True
        assert self.validator.validate_ip("192.168.1.1") is True

    def test_validate_ip_blacklisted(self):
        """Test validation rejects blacklisted IPs."""
        with pytest.raises(UnauthorizedTargetError):
            self.validator.validate_ip("127.0.0.1")

        with pytest.raises(UnauthorizedTargetError):
            self.validator.validate_ip("169.254.0.1")

    def test_validate_ip_invalid_format(self):
        """Test validation rejects invalid IP formats."""
        with pytest.raises(InvalidTargetError):
            self.validator.validate_ip("not-an-ip")

        with pytest.raises(InvalidTargetError):
            self.validator.validate_ip("256.256.256.256")

    def test_validate_hostname(self):
        """Test hostname validation."""
        # Should pass when no domains configured (permissive)
        assert self.validator.validate_hostname("example.com") is True
        assert self.validator.validate_hostname("sub.example.com") is True

    def test_validate_target_ip(self):
        """Test target validation with IP addresses."""
        assert self.validator.validate_target("192.168.1.100") is True

        with pytest.raises(UnauthorizedTargetError):
            self.validator.validate_target("127.0.0.1")

    def test_validate_target_url(self):
        """Test target validation with URLs."""
        assert self.validator.validate_target("http://192.168.1.100") is True
        assert self.validator.validate_target("https://example.com") is True

    def test_validate_target_cidr(self):
        """Test target validation with CIDR ranges."""
        assert self.validator.validate_target("192.168.1.0/24") is True

    def test_validate_command_args_safe(self):
        """Test command argument validation with safe args."""
        safe_args = ["-p", "80,443", "-sV", "192.168.1.1"]
        assert self.validator.validate_command_args(safe_args) is True

    def test_validate_command_args_dangerous(self):
        """Test command argument validation rejects dangerous patterns."""
        dangerous_args = ["; rm -rf /"]
        with pytest.raises(InvalidTargetError):
            self.validator.validate_command_args(dangerous_args)

        dangerous_args = ["| sh"]
        with pytest.raises(InvalidTargetError):
            self.validator.validate_command_args(dangerous_args)

        dangerous_args = ["$(whoami)"]
        with pytest.raises(InvalidTargetError):
            self.validator.validate_command_args(dangerous_args)

    def test_log_tool_execution(self):
        """Test tool execution logging."""
        # Should not raise exception
        self.validator.log_tool_execution(
            tool_name="nmap",
            target="192.168.1.100",
            params={"scan_type": "sV"},
            user_id="test_user",
            result="success"
        )


class TestSafetyValidatorWithConfig:
    """Test SafetyValidator with custom configuration."""

    def test_custom_authorized_networks(self):
        """Test validator with custom authorized networks."""
        validator = SafetyValidator()
        # Default config should allow private networks
        assert validator.validate_ip("10.1.1.1") is True

    def test_empty_target(self):
        """Test validation with empty target."""
        validator = SafetyValidator()
        with pytest.raises(InvalidTargetError):
            validator.validate_target("")

        with pytest.raises(InvalidTargetError):
            validator.validate_target(None)
