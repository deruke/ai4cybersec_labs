"""
Cloud security assessment tools.

Includes: prowler, scout-suite
"""

from typing import Dict, List, Any
import mcp.types as types

from ..logging_config import get_logger
from ..safety import get_validator
from .network import execute_command

logger = get_logger(__name__)


async def prowler_scan(
    provider: str = "aws",
    profile: str = "default",
    services: str = "",
    severity: str = ""
) -> Dict[str, Any]:
    """
    Cloud security assessment with Prowler.

    Args:
        provider: Cloud provider (aws, azure, gcp)
        profile: AWS profile name or Azure subscription
        services: Specific services to scan
        severity: Severity filter (critical, high, medium, low)

    Returns:
        Security assessment results
    """
    validator = get_validator()

    try:
        cmd = ["prowler", provider]

        if provider == "aws":
            cmd.extend(["-p", profile])

        if services:
            cmd.extend(["-s", services])

        if severity:
            cmd.extend(["--severity", severity])

        cmd.extend(["-M", "json"])

        validator.log_tool_execution(
            "prowler",
            f"{provider}:{profile}",
            {"services": services, "severity": severity}
        )

        result = await execute_command(cmd, timeout=1800, tool_name="prowler")

        return {
            "tool": "prowler",
            "provider": provider,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Prowler error: {e}")
        return {
            "tool": "prowler",
            "provider": provider,
            "success": False,
            "error": str(e)
        }


async def scoutsuite_scan(
    provider: str = "aws",
    profile: str = "default",
    services: str = ""
) -> Dict[str, Any]:
    """
    Multi-cloud security auditing with Scout Suite.

    Args:
        provider: Cloud provider (aws, azure, gcp, alibaba, oci)
        profile: Cloud credentials profile
        services: Specific services to audit

    Returns:
        Security audit results
    """
    validator = get_validator()

    try:
        cmd = [
            "scout",
            provider,
            "--profile", profile,
            "--report-dir", "/tmp/scoutsuite",
            "--no-browser"
        ]

        if services:
            cmd.extend(["--services", services])

        validator.log_tool_execution(
            "scoutsuite",
            f"{provider}:{profile}",
            {"services": services}
        )

        result = await execute_command(cmd, timeout=1800, tool_name="scoutsuite")

        return {
            "tool": "scoutsuite",
            "provider": provider,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Scout Suite error: {e}")
        return {
            "tool": "scoutsuite",
            "provider": provider,
            "success": False,
            "error": str(e)
        }


def list_tools() -> List[types.Tool]:
    """List all cloud security tools."""
    return [
        types.Tool(
            name="prowler_scan",
            description="Cloud security assessment tool for AWS, Azure, and GCP. Performs CIS benchmark checks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Cloud provider (aws, azure, gcp)",
                        "default": "aws"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Profile name",
                        "default": "default"
                    },
                    "services": {
                        "type": "string",
                        "description": "Specific services to scan",
                        "default": ""
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity filter",
                        "default": ""
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="scoutsuite_scan",
            description="Multi-cloud security auditing tool for AWS, Azure, GCP, Alibaba Cloud, and Oracle Cloud.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Cloud provider",
                        "default": "aws"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Credentials profile",
                        "default": "default"
                    },
                    "services": {
                        "type": "string",
                        "description": "Specific services",
                        "default": ""
                    }
                },
                "required": []
            }
        )
    ]


def get_tools() -> List[Dict[str, Any]]:
    """Get tool handlers for registration."""
    return [
        {"name": "prowler_scan", "handler": prowler_scan},
        {"name": "scoutsuite_scan", "handler": scoutsuite_scan},
    ]
