"""
Safety validation and authorization checks for security training tools.

This module ensures all tool executions are authorized and within scope.
"""

import ipaddress
import re
from typing import List, Optional
from urllib.parse import urlparse
import yaml
import os
from datetime import datetime

from .logging_config import get_logger

logger = get_logger(__name__)


class UnauthorizedTargetError(Exception):
    """Raised when a target is not authorized for testing."""
    pass


class InvalidTargetError(Exception):
    """Raised when a target format is invalid."""
    pass


class SafetyValidator:
    """Validates targets against authorized networks and blacklists."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the safety validator.

        Args:
            config_path: Path to configuration file. If None, uses environment variables.
        """
        self.authorized_networks: List[ipaddress.IPv4Network] = []
        self.blacklisted_networks: List[ipaddress.IPv4Network] = []
        self.authorized_domains: List[str] = []

        # Default blacklisted networks (RFC 1918 private + sensitive ranges)
        default_blacklist = [
            "169.254.0.0/16",  # Link-local
            "224.0.0.0/4",     # Multicast
            "240.0.0.0/4",     # Reserved
        ]

        # Load configuration
        if config_path and os.path.exists(config_path):
            self._load_from_config(config_path)
        else:
            self._load_from_environment()

        # Add default blacklist
        for network in default_blacklist:
            try:
                self.blacklisted_networks.append(ipaddress.IPv4Network(network))
            except ValueError:
                pass

        logger.info(f"SafetyValidator initialized with {len(self.authorized_networks)} authorized networks")

    def _load_from_config(self, config_path: str):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            security_config = config.get('security', {})

            # Load authorized networks
            for network in security_config.get('authorized_networks', []):
                try:
                    self.authorized_networks.append(ipaddress.IPv4Network(network))
                except ValueError as e:
                    logger.error(f"Invalid authorized network {network}: {e}")

            # Load blacklisted networks
            for network in security_config.get('blacklisted_networks', []):
                try:
                    self.blacklisted_networks.append(ipaddress.IPv4Network(network))
                except ValueError as e:
                    logger.error(f"Invalid blacklisted network {network}: {e}")

            # Load authorized domains
            self.authorized_domains = security_config.get('authorized_domains', [])

        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            raise

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # AUTHORIZED_NETWORKS should be comma-separated like "10.0.0.0/8,172.16.0.0/12"
        authorized = os.getenv('AUTHORIZED_NETWORKS', '10.0.0.0/8,172.16.0.0/12,192.168.0.0/16')
        for network in authorized.split(','):
            network = network.strip()
            if network:
                try:
                    self.authorized_networks.append(ipaddress.IPv4Network(network))
                except ValueError as e:
                    logger.error(f"Invalid authorized network {network}: {e}")

        # BLACKLISTED_NETWORKS
        blacklisted = os.getenv('BLACKLISTED_NETWORKS', '127.0.0.0/8')
        for network in blacklisted.split(','):
            network = network.strip()
            if network:
                try:
                    self.blacklisted_networks.append(ipaddress.IPv4Network(network))
                except ValueError as e:
                    logger.error(f"Invalid blacklisted network {network}: {e}")

        # AUTHORIZED_DOMAINS
        domains = os.getenv('AUTHORIZED_DOMAINS', '')
        if domains:
            self.authorized_domains = [d.strip() for d in domains.split(',') if d.strip()]

    def validate_ip(self, ip_str: str) -> bool:
        """
        Validate an IP address against authorized and blacklisted networks.

        Args:
            ip_str: IP address string

        Returns:
            True if IP is authorized

        Raises:
            UnauthorizedTargetError: If IP is not authorized
            InvalidTargetError: If IP format is invalid
        """
        try:
            ip = ipaddress.IPv4Address(ip_str)
        except ValueError:
            raise InvalidTargetError(f"Invalid IP address format: {ip_str}")

        # Check blacklist first
        for network in self.blacklisted_networks:
            if ip in network:
                logger.warning(f"IP {ip_str} is in blacklisted network {network}")
                raise UnauthorizedTargetError(f"Target {ip_str} is in blacklisted network")

        # Check if in authorized networks
        # If no authorized_networks configured, allow all IPs (permissive for training)
        if not self.authorized_networks:
            logger.info(f"IP {ip_str} validated (no network restrictions configured)")
            return True

        authorized = False
        for network in self.authorized_networks:
            if ip in network:
                authorized = True
                break

        if not authorized:
            logger.warning(f"IP {ip_str} is not in any authorized network")
            raise UnauthorizedTargetError(f"Target {ip_str} is not in authorized networks")

        logger.info(f"IP {ip_str} validated successfully")
        return True

    def validate_hostname(self, hostname: str) -> bool:
        """
        Validate a hostname against authorized domains.

        Args:
            hostname: Hostname string

        Returns:
            True if hostname is authorized

        Raises:
            UnauthorizedTargetError: If hostname is not authorized
        """
        # Remove protocol if present
        if '://' in hostname:
            parsed = urlparse(hostname)
            hostname = parsed.netloc or parsed.path

        # Remove port if present
        hostname = hostname.split(':')[0]

        # If no authorized domains configured, allow all (permissive for training)
        if not self.authorized_domains:
            logger.info(f"Hostname {hostname} validated (no domain restrictions)")
            return True

        # Check if hostname matches authorized domains
        for domain in self.authorized_domains:
            if hostname == domain or hostname.endswith('.' + domain):
                logger.info(f"Hostname {hostname} validated against domain {domain}")
                return True

        logger.warning(f"Hostname {hostname} is not in authorized domains")
        raise UnauthorizedTargetError(f"Hostname {hostname} is not in authorized domains")

    def validate_target(self, target: str) -> bool:
        """
        Validate any target (IP, hostname, URL, or CIDR range).

        Args:
            target: Target string (IP, hostname, URL, or CIDR)

        Returns:
            True if target is authorized

        Raises:
            UnauthorizedTargetError: If target is not authorized
            InvalidTargetError: If target format is invalid
        """
        if not target or not isinstance(target, str):
            raise InvalidTargetError("Target must be a non-empty string")

        target = target.strip()

        # Log validation attempt
        logger.info(f"Validating target: {target}")

        # Try parsing as URL first
        if '://' in target:
            parsed = urlparse(target)
            hostname = parsed.netloc or parsed.path
            hostname = hostname.split(':')[0]

            # Try as IP
            try:
                return self.validate_ip(hostname)
            except InvalidTargetError:
                # Not an IP, try as hostname
                return self.validate_hostname(hostname)

        # Try parsing as CIDR range
        if '/' in target:
            try:
                network = ipaddress.IPv4Network(target)
                # Validate the network itself is in authorized range
                # For simplicity, check if first IP is authorized
                return self.validate_ip(str(network.network_address))
            except ValueError:
                raise InvalidTargetError(f"Invalid CIDR notation: {target}")

        # Try parsing as IP address
        try:
            return self.validate_ip(target)
        except InvalidTargetError:
            # Not an IP, try as hostname
            return self.validate_hostname(target)

    def validate_command_args(self, args: List[str]) -> bool:
        """
        Validate command arguments for dangerous patterns.

        Args:
            args: List of command arguments

        Returns:
            True if arguments are safe

        Raises:
            InvalidTargetError: If dangerous patterns detected
        """
        dangerous_patterns = [
            r';\s*rm\s+-rf',  # Command injection
            r'\|\s*sh',       # Pipe to shell
            r'&&\s*',         # Command chaining
            r'\$\(',          # Command substitution
            r'`',             # Backtick command substitution
        ]

        args_str = ' '.join(args)

        for pattern in dangerous_patterns:
            if re.search(pattern, args_str):
                logger.error(f"Dangerous pattern detected in args: {pattern}")
                raise InvalidTargetError(f"Dangerous command pattern detected")

        return True

    def log_tool_execution(self, tool_name: str, target: str, params: dict,
                          user_id: str = "unknown", result: str = "pending"):
        """
        Log tool execution for audit trail.

        Args:
            tool_name: Name of the tool being executed
            target: Target of the scan/test
            params: Tool parameters
            user_id: User identifier
            result: Execution result status
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "target": target,
            "parameters": params,
            "user_id": user_id,
            "result": result,
        }

        logger.info(f"AUDIT: {log_entry}")


# Global validator instance
_validator: Optional[SafetyValidator] = None


def get_validator() -> SafetyValidator:
    """Get the global SafetyValidator instance."""
    global _validator
    if _validator is None:
        config_path = os.getenv('CONFIG_PATH', '/app/config/tools.yaml')
        if os.path.exists(config_path):
            _validator = SafetyValidator(config_path)
        else:
            _validator = SafetyValidator()
    return _validator
