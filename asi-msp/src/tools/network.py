"""
Network reconnaissance and scanning tools.

Includes: nmap, masscan, rustscan, amass, subfinder, nuclei, fierce, dnsenum,
autorecon, theharvester, responder, netexec, enum4linux-ng
"""

import asyncio
import json
import subprocess
import shlex
from typing import Dict, List, Any, Optional
from datetime import datetime

import mcp.types as types

from ..logging_config import get_logger, get_audit_logger
from ..safety import get_validator, UnauthorizedTargetError, InvalidTargetError

logger = get_logger(__name__)
audit_logger = get_audit_logger()


async def execute_command(
    cmd: List[str],
    timeout: int = 300,
    tool_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Execute a command with timeout and error handling.

    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds
        tool_name: Name of the tool for logging

    Returns:
        Dict with stdout, stderr, returncode, and execution time
    """
    start_time = datetime.utcnow()

    try:
        logger.info(f"Executing {tool_name}: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"{tool_name} execution exceeded {timeout} seconds")

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "stdout": stdout.decode('utf-8', errors='ignore'),
            "stderr": stderr.decode('utf-8', errors='ignore'),
            "returncode": process.returncode,
            "duration_seconds": duration,
            "success": process.returncode == 0
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Error executing {tool_name}: {e}")
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "duration_seconds": duration,
            "success": False,
            "error": str(e)
        }


# Tool implementations

async def nmap_scan(
    target: str,
    scan_type: str = "sV",
    ports: str = "",
    arguments: str = ""
) -> Dict[str, Any]:
    """
    Execute nmap network scan.

    Args:
        target: IP address, hostname, or CIDR range
        scan_type: Scan type (sS, sT, sV, sC, A, etc.)
        ports: Port specification (e.g., "80,443" or "1-1000")
        arguments: Additional nmap arguments

    Returns:
        Scan results
    """
    validator = get_validator()

    try:
        # Validate target
        validator.validate_target(target)

        # Build command
        cmd = ["nmap", f"-{scan_type}"]

        if ports:
            cmd.extend(["-p", ports])

        if arguments:
            # Parse additional arguments safely
            validator.validate_command_args(shlex.split(arguments))
            cmd.extend(shlex.split(arguments))

        cmd.extend(["-oX", "-", target])  # XML output to stdout

        # Log execution
        validator.log_tool_execution(
            "nmap",
            target,
            {"scan_type": scan_type, "ports": ports, "arguments": arguments}
        )

        # Execute
        result = await execute_command(cmd, timeout=600, tool_name="nmap")

        # Parse XML output into structured data
        import xml.etree.ElementTree as ET
        hosts = []

        if result["success"] and result["stdout"]:
            try:
                root = ET.fromstring(result["stdout"])

                # Parse each host
                for host_elem in root.findall('.//host'):
                    host_data = {
                        "addresses": [],
                        "hostnames": [],
                        "ports": [],
                        "state": None
                    }

                    # Get addresses
                    for addr in host_elem.findall('.//address'):
                        host_data["addresses"].append({
                            "addr": addr.get("addr"),
                            "type": addr.get("addrtype")
                        })

                    # Get hostnames
                    for hostname in host_elem.findall('.//hostname'):
                        host_data["hostnames"].append({
                            "name": hostname.get("name"),
                            "type": hostname.get("type")
                        })

                    # Get host state
                    status = host_elem.find('.//status')
                    if status is not None:
                        host_data["state"] = status.get("state")

                    # Get ports
                    for port in host_elem.findall('.//port'):
                        port_data = {
                            "port": port.get("portid"),
                            "protocol": port.get("protocol"),
                            "state": None,
                            "service": None
                        }

                        state = port.find('state')
                        if state is not None:
                            port_data["state"] = state.get("state")

                        service = port.find('service')
                        if service is not None:
                            port_data["service"] = {
                                "name": service.get("name"),
                                "product": service.get("product"),
                                "version": service.get("version"),
                                "extrainfo": service.get("extrainfo")
                            }

                        host_data["ports"].append(port_data)

                    hosts.append(host_data)

            except Exception as parse_error:
                logger.error(f"Error parsing nmap XML: {parse_error}")
                # Fall back to raw output if parsing fails
                return {
                    "tool": "nmap",
                    "target": target,
                    "scan_type": scan_type,
                    "success": result["success"],
                    "xml_output": result["stdout"],
                    "parse_error": str(parse_error),
                    "duration_seconds": result["duration_seconds"]
                }

        return {
            "tool": "nmap",
            "target": target,
            "scan_type": scan_type,
            "success": result["success"],
            "hosts": hosts,
            "hosts_count": len(hosts),
            "scan_info": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except (UnauthorizedTargetError, InvalidTargetError) as e:
        logger.error(f"Target validation failed: {e}")
        return {
            "tool": "nmap",
            "target": target,
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Nmap scan error: {e}")
        return {
            "tool": "nmap",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def masscan_scan(
    target: str,
    ports: str = "1-1000",
    rate: int = 1000
) -> Dict[str, Any]:
    """
    Execute masscan high-speed port scan.

    Args:
        target: IP address or CIDR range
        ports: Port range (e.g., "1-65535" or "80,443")
        rate: Packets per second

    Returns:
        Scan results
    """
    validator = get_validator()

    try:
        validator.validate_target(target)

        cmd = [
            "masscan",
            target,
            "-p", ports,
            "--rate", str(rate),
            "-oJ", "-"  # JSON output to stdout
        ]

        validator.log_tool_execution(
            "masscan",
            target,
            {"ports": ports, "rate": rate}
        )

        result = await execute_command(cmd, timeout=600, tool_name="masscan")

        return {
            "tool": "masscan",
            "target": target,
            "ports": ports,
            "rate": rate,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Masscan error: {e}")
        return {
            "tool": "masscan",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def rustscan_scan(
    target: str,
    ports: str = "",
    ulimit: int = 5000
) -> Dict[str, Any]:
    """
    Execute rustscan fast port scanner.

    Args:
        target: IP address or hostname
        ports: Port range (empty for all)
        ulimit: File descriptor limit

    Returns:
        Scan results
    """
    validator = get_validator()

    try:
        validator.validate_target(target)

        cmd = ["rustscan", "-a", target, "--ulimit", str(ulimit)]

        if ports:
            cmd.extend(["-p", ports])

        validator.log_tool_execution(
            "rustscan",
            target,
            {"ports": ports, "ulimit": ulimit}
        )

        result = await execute_command(cmd, timeout=300, tool_name="rustscan")

        return {
            "tool": "rustscan",
            "target": target,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Rustscan error: {e}")
        return {
            "tool": "rustscan",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def subfinder_scan(
    domain: str,
    sources: str = ""
) -> Dict[str, Any]:
    """
    Execute subfinder for passive subdomain discovery.

    Args:
        domain: Target domain
        sources: Comma-separated list of sources

    Returns:
        Discovered subdomains
    """
    validator = get_validator()

    try:
        validator.validate_hostname(domain)

        cmd = ["subfinder", "-d", domain, "-json"]

        if sources:
            cmd.extend(["-sources", sources])

        validator.log_tool_execution(
            "subfinder",
            domain,
            {"sources": sources}
        )

        result = await execute_command(cmd, timeout=300, tool_name="subfinder")

        return {
            "tool": "subfinder",
            "domain": domain,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Subfinder error: {e}")
        return {
            "tool": "subfinder",
            "domain": domain,
            "success": False,
            "error": str(e)
        }


async def nuclei_scan(
    target: str,
    templates: str = "",
    severity: str = "",
    profile: str = "pentest"
) -> Dict[str, Any]:
    """
    Execute nuclei vulnerability scanner with pentest profile by default.

    Args:
        target: Target URL or host
        templates: Template tags or paths (overrides profile if specified)
        severity: Severity filter (info, low, medium, high, critical)
        profile: Profile to use (default: pentest). Set to empty string to disable.

    Returns:
        Vulnerability scan results
    """
    import tempfile
    import os
    import json

    validator = get_validator()

    # Create temporary file for JSON results
    output_file = tempfile.mktemp(suffix=".jsonl", prefix="nuclei_", dir="/tmp")

    try:
        validator.validate_target(target)

        cmd = ["nuclei", "-u", target, "-jsonl", "-o", output_file]

        # Use templates if specified, otherwise use profile
        if templates:
            cmd.extend(["-t", templates])
        elif profile:
            # Use the pentest profile from nuclei-templates
            cmd.extend(["-profile", profile])

        if severity:
            cmd.extend(["-s", severity])

        validator.log_tool_execution(
            "nuclei",
            target,
            {"templates": templates, "severity": severity, "profile": profile}
        )

        result = await execute_command(cmd, timeout=600, tool_name="nuclei")

        # Read and parse JSONL results
        findings = []
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                findings.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            finally:
                # Clean up temp file
                try:
                    os.remove(output_file)
                except:
                    pass

        return {
            "tool": "nuclei",
            "target": target,
            "success": result["success"],
            "findings": findings,
            "findings_count": len(findings),
            "scan_info": result["stderr"],  # Nuclei puts scan info in stderr
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Nuclei error: {e}")
        # Clean up on error
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except:
            pass
        return {
            "tool": "nuclei",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def theharvester_scan(
    domain: str,
    sources: str = "all",
    limit: int = 500
) -> Dict[str, Any]:
    """
    Execute theHarvester for OSINT gathering.

    Args:
        domain: Target domain
        sources: Data sources (google, bing, linkedin, etc.)
        limit: Result limit

    Returns:
        OSINT results
    """
    validator = get_validator()

    try:
        validator.validate_hostname(domain)

        cmd = [
            "theHarvester",
            "-d", domain,
            "-b", sources,
            "-l", str(limit)
        ]

        validator.log_tool_execution(
            "theharvester",
            domain,
            {"sources": sources, "limit": limit}
        )

        result = await execute_command(cmd, timeout=300, tool_name="theharvester")

        return {
            "tool": "theharvester",
            "domain": domain,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"theHarvester error: {e}")
        return {
            "tool": "theharvester",
            "domain": domain,
            "success": False,
            "error": str(e)
        }


# MCP Tool definitions

def list_tools() -> List[types.Tool]:
    """List all network reconnaissance tools."""
    return [
        types.Tool(
            name="nmap_scan",
            description="Network scanning and service detection with nmap. Supports various scan types including service version detection, OS detection, and script scanning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "IP address, hostname, or CIDR range to scan"
                    },
                    "scan_type": {
                        "type": "string",
                        "description": "Scan type: sS (SYN), sT (TCP), sV (version), sC (scripts), A (aggressive)",
                        "default": "sV"
                    },
                    "ports": {
                        "type": "string",
                        "description": "Port specification (e.g., '80,443' or '1-1000')",
                        "default": ""
                    },
                    "arguments": {
                        "type": "string",
                        "description": "Additional nmap arguments",
                        "default": ""
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="masscan_scan",
            description="High-speed TCP port scanner. Can scan the entire Internet in under 6 minutes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "IP address or CIDR range"
                    },
                    "ports": {
                        "type": "string",
                        "description": "Port range (e.g., '1-65535' or '80,443')",
                        "default": "1-1000"
                    },
                    "rate": {
                        "type": "integer",
                        "description": "Packets per second",
                        "default": 1000
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="rustscan_scan",
            description="Fast port scanner that feeds results to nmap. Much faster than nmap alone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "IP address or hostname"
                    },
                    "ports": {
                        "type": "string",
                        "description": "Port range (empty for all ports)",
                        "default": ""
                    },
                    "ulimit": {
                        "type": "integer",
                        "description": "File descriptor limit",
                        "default": 5000
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="subfinder_scan",
            description="Passive subdomain discovery using multiple sources (CertSpotter, SecurityTrails, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Target domain"
                    },
                    "sources": {
                        "type": "string",
                        "description": "Comma-separated list of sources",
                        "default": ""
                    }
                },
                "required": ["domain"]
            }
        ),
        types.Tool(
            name="nuclei_scan",
            description="Fast vulnerability scanner using the pentest profile by default. Detects CVEs, misconfigurations, and security issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL or host"
                    },
                    "templates": {
                        "type": "string",
                        "description": "Template tags or paths (e.g., 'cves', 'exposures'). Overrides profile if specified.",
                        "default": ""
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity filter: info, low, medium, high, critical",
                        "default": ""
                    },
                    "profile": {
                        "type": "string",
                        "description": "Profile to use (default: pentest). Options: pentest, bug-bounty, web, cloud, network. Set to empty string to run all templates.",
                        "default": "pentest"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="theharvester_scan",
            description="OSINT tool for gathering emails, subdomains, IPs, and URLs from public sources.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Target domain"
                    },
                    "sources": {
                        "type": "string",
                        "description": "Data sources (google, bing, linkedin, etc.)",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Result limit",
                        "default": 500
                    }
                },
                "required": ["domain"]
            }
        )
    ]


def get_tools() -> List[Dict[str, Any]]:
    """Get tool handlers for registration."""
    return [
        {"name": "nmap_scan", "handler": nmap_scan},
        {"name": "masscan_scan", "handler": masscan_scan},
        {"name": "rustscan_scan", "handler": rustscan_scan},
        {"name": "subfinder_scan", "handler": subfinder_scan},
        {"name": "nuclei_scan", "handler": nuclei_scan},
        {"name": "theharvester_scan", "handler": theharvester_scan},
    ]
