"""
Binary analysis and reverse engineering tools.

Includes: strings, binwalk, radare2
"""

from typing import Dict, List, Any
import mcp.types as types

from ..logging_config import get_logger
from ..safety import get_validator
from .network import execute_command

logger = get_logger(__name__)


async def strings_analyze(
    file_path: str,
    min_length: int = 4,
    encoding: str = "s"
) -> Dict[str, Any]:
    """
    Extract printable strings from binary files.

    Args:
        file_path: Path to binary file
        min_length: Minimum string length
        encoding: Encoding type (s=single-7-bit, S=single-8-bit, b=16-bit, l=32-bit)

    Returns:
        Extracted strings
    """
    try:
        cmd = [
            "strings",
            f"-{encoding}",
            "-n", str(min_length),
            file_path
        ]

        result = await execute_command(cmd, timeout=120, tool_name="strings")

        return {
            "tool": "strings",
            "file": file_path,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Strings error: {e}")
        return {
            "tool": "strings",
            "file": file_path,
            "success": False,
            "error": str(e)
        }


async def binwalk_analyze(
    file_path: str,
    extract: bool = False,
    signature: bool = True
) -> Dict[str, Any]:
    """
    Firmware analysis and extraction with binwalk.

    Args:
        file_path: Path to firmware file
        extract: Extract discovered files
        signature: Scan for signatures

    Returns:
        Analysis results
    """
    try:
        cmd = ["binwalk"]

        if extract:
            cmd.append("-e")

        if signature:
            cmd.append("-B")

        cmd.append(file_path)

        result = await execute_command(cmd, timeout=300, tool_name="binwalk")

        return {
            "tool": "binwalk",
            "file": file_path,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Binwalk error: {e}")
        return {
            "tool": "binwalk",
            "file": file_path,
            "success": False,
            "error": str(e)
        }


async def radare2_analyze(
    file_path: str,
    command: str = "aaa;pdf"
) -> Dict[str, Any]:
    """
    Binary analysis with radare2.

    Args:
        file_path: Path to binary file
        command: Radare2 commands to execute

    Returns:
        Analysis results
    """
    try:
        cmd = [
            "r2",
            "-q",  # Quiet mode
            "-c", command,
            file_path
        ]

        result = await execute_command(cmd, timeout=300, tool_name="radare2")

        return {
            "tool": "radare2",
            "file": file_path,
            "command": command,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Radare2 error: {e}")
        return {
            "tool": "radare2",
            "file": file_path,
            "success": False,
            "error": str(e)
        }


def list_tools() -> List[types.Tool]:
    """List all binary analysis tools."""
    return [
        types.Tool(
            name="strings_analyze",
            description="Extract printable strings from binary files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to binary file"
                    },
                    "min_length": {
                        "type": "integer",
                        "description": "Minimum string length",
                        "default": 4
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Encoding type",
                        "default": "s"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="binwalk_analyze",
            description="Firmware analysis and extraction tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to firmware file"
                    },
                    "extract": {
                        "type": "boolean",
                        "description": "Extract discovered files",
                        "default": False
                    },
                    "signature": {
                        "type": "boolean",
                        "description": "Scan for signatures",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="radare2_analyze",
            description="Binary analysis framework.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to binary"
                    },
                    "command": {
                        "type": "string",
                        "description": "Radare2 commands",
                        "default": "aaa;pdf"
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


def get_tools() -> List[Dict[str, Any]]:
    """Get tool handlers for registration."""
    return [
        {"name": "strings_analyze", "handler": strings_analyze},
        {"name": "binwalk_analyze", "handler": binwalk_analyze},
        {"name": "radare2_analyze", "handler": radare2_analyze},
    ]
