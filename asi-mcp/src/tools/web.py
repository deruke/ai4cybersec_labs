"""
Web application security testing tools.

Includes: gobuster, feroxbuster, dirsearch, ffuf, dirb, httpx, katana,
nikto, sqlmap, wpscan, arjun, paramspider, dalfox, wafw00f
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

import mcp.types as types

from ..logging_config import get_logger
from ..safety import get_validator, UnauthorizedTargetError, InvalidTargetError
from .network import execute_command

logger = get_logger(__name__)


async def gobuster_scan(
    url: str,
    wordlist: str = "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
    extensions: str = "",
    threads: int = 10,
    exclude_length: str = "",
    status_codes_blacklist: str = ""
) -> Dict[str, Any]:
    """
    Directory and file brute-forcing with gobuster.

    Args:
        url: Target URL
        wordlist: Path to wordlist file
        extensions: File extensions (e.g., "php,html,txt")
        threads: Number of concurrent threads
        exclude_length: Comma-separated list of lengths to exclude (e.g., "110,123")
        status_codes_blacklist: Comma-separated status codes to exclude (e.g., "302,404")

    Returns:
        Discovered directories and files
    """
    import tempfile
    import os

    validator = get_validator()

    # Create temporary output file
    output_file = tempfile.mktemp(suffix=".txt", prefix="gobuster_", dir="/tmp")

    try:
        validator.validate_target(url)

        # Check if wordlist exists, fall back to dirb if not
        if not os.path.exists(wordlist):
            fallback_wordlist = "/usr/share/dirb/wordlists/common.txt"
            if os.path.exists(fallback_wordlist):
                logger.warning(f"Wordlist {wordlist} not found, using fallback: {fallback_wordlist}")
                wordlist = fallback_wordlist
            else:
                raise FileNotFoundError(f"Wordlist not found: {wordlist}")

        # Build gobuster command with proper flags
        cmd = [
            "gobuster", "dir",
            "--url", url,
            "--wordlist", wordlist,
            "--output", output_file,
            "--threads", str(threads),
            "--useragent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
            "--no-error"   # Don't display errors
        ]

        if extensions:
            cmd.extend(["--extensions", extensions])

        if exclude_length:
            cmd.extend(["--exclude-length", exclude_length])

        if status_codes_blacklist:
            cmd.extend(["--status-codes-blacklist", status_codes_blacklist])

        validator.log_tool_execution(
            "gobuster",
            url,
            {
                "wordlist": wordlist,
                "extensions": extensions,
                "threads": threads,
                "exclude_length": exclude_length,
                "status_codes_blacklist": status_codes_blacklist
            }
        )

        result = await execute_command(cmd, timeout=600, tool_name="gobuster")

        # Parse gobuster output file into structured findings
        findings = []
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('=') and '(Status:' in line:
                            # Gobuster output format: /path (Status: 200) [Size: 1234]
                            parts = line.split()
                            if len(parts) >= 1:
                                path = parts[0]
                                status = None
                                size = None

                                # Extract status code
                                try:
                                    status = int(line.split('(Status:')[1].split(')')[0].strip())
                                except:
                                    pass

                                # Extract size
                                if '[Size:' in line:
                                    try:
                                        size = int(line.split('[Size:')[1].split(']')[0].strip())
                                    except:
                                        pass

                                findings.append({
                                    "path": path,
                                    "status_code": status,
                                    "size": size,
                                    "full_line": line
                                })
            finally:
                # Clean up temp file
                try:
                    os.remove(output_file)
                except:
                    pass

        # Check if scan failed due to wildcard detection
        scan_info = result["stderr"]
        if "Please exclude the response length or the status code" in scan_info and not exclude_length and not status_codes_blacklist:
            # Auto-detect and retry with exclusions
            import re

            # Extract status code and length from error message
            # Format: "=> 302 (redirect...) (Length: 110)"
            status_match = re.search(r'=>\s+(\d+)', scan_info)
            length_match = re.search(r'\(Length:\s+(\d+)\)', scan_info)

            auto_exclude_length = length_match.group(1) if length_match else ""
            auto_status_blacklist = status_match.group(1) if status_match else ""

            if auto_exclude_length or auto_status_blacklist:
                logger.info(f"Wildcard detected, retrying with exclusions: length={auto_exclude_length}, status={auto_status_blacklist}")

                # Retry with auto-detected exclusions
                return await gobuster_scan(
                    url=url,
                    wordlist=wordlist,
                    extensions=extensions,
                    threads=threads,
                    exclude_length=auto_exclude_length,
                    status_codes_blacklist=auto_status_blacklist
                )
            else:
                # Could not parse exclusions, return error
                return {
                    "tool": "gobuster",
                    "target": url,
                    "success": False,
                    "error": "Wildcard response detected. Could not auto-detect exclusions.",
                    "suggestion": "Manually add exclude_length or status_codes_blacklist parameter",
                    "scan_info": scan_info,
                    "duration_seconds": result["duration_seconds"]
                }

        return {
            "tool": "gobuster",
            "target": url,
            "success": result["success"],
            "findings": findings,
            "findings_count": len(findings),
            "scan_info": scan_info,
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Gobuster error: {e}")
        # Clean up on error
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except:
            pass
        return {
            "tool": "gobuster",
            "target": url,
            "success": False,
            "error": str(e)
        }


async def nikto_scan(
    target: str
) -> Dict[str, Any]:
    """
    Web server vulnerability scanner with nikto.

    Args:
        target: Target URL (e.g., https://example.com or http://example.com)

    Returns:
        Vulnerability scan results
    """
    validator = get_validator()

    try:
        validator.validate_target(target)

        # Nikto requires an output file for JSON format
        import tempfile
        import os
        import json

        output_file = tempfile.mktemp(suffix=".json", prefix="nikto_", dir="/tmp/scans")

        # Nikto with maxtime to ensure it completes before timeout
        # maxtime=1500 (25 minutes) gives it time to finish and write JSON
        cmd = [
            "nikto",
            "-h", target,
            "-maxtime", "1500",
            "-F", "json",
            "-o", output_file
        ]

        validator.log_tool_execution(
            "nikto",
            target,
            {"maxtime": 1500}
        )

        result = await execute_command(cmd, timeout=1800, tool_name="nikto")

        # Parse JSON output from file (if it exists)
        findings = []
        vulnerabilities = []

        try:
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, 'r') as f:
                    content = f.read()

                # Nikto JSON output may be single object or multiple lines
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        findings.append(data)
                        # Extract vulnerabilities from nikto JSON structure
                        if "vulnerabilities" in data:
                            vulnerabilities = data["vulnerabilities"]
                    elif isinstance(data, list):
                        findings = data
                        for item in data:
                            if isinstance(item, dict) and "vulnerabilities" in item:
                                vulnerabilities.extend(item["vulnerabilities"])
                except json.JSONDecodeError:
                    # Try line-by-line parsing
                    for line in content.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                findings.append(data)
                                if isinstance(data, dict) and "vulnerabilities" in data:
                                    vulnerabilities.extend(data["vulnerabilities"])
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.warning(f"Could not read/parse nikto output file: {e}")

        # If JSON file wasn't created or is empty, parse stdout
        if not findings and result.get("stdout"):
            stdout_findings = []
            for line in result["stdout"].split('\n'):
                line = line.strip()
                # Parse nikto text output (lines starting with +)
                if line.startswith('+ /') or line.startswith('+ http'):
                    stdout_findings.append({
                        "type": "nikto_finding",
                        "description": line[2:].strip(),  # Remove "+ " prefix
                        "source": "stdout"
                    })

            if stdout_findings:
                findings = stdout_findings
                vulnerabilities = stdout_findings

        return {
            "tool": "nikto",
            "target": target,
            "success": result["success"] or len(findings) > 0,  # Success if we got findings
            "findings": findings,
            "vulnerabilities": vulnerabilities,
            "vulnerabilities_count": len(vulnerabilities),
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Nikto error: {e}")
        return {
            "tool": "nikto",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def sqlmap_scan(
    url: str,
    data: str = "",
    cookie: str = "",
    level: int = 1,
    risk: int = 1
) -> Dict[str, Any]:
    """
    SQL injection detection and exploitation with sqlmap.

    Args:
        url: Target URL
        data: POST data
        cookie: HTTP Cookie header value
        level: Level of tests (1-5)
        risk: Risk of tests (1-3)

    Returns:
        SQL injection scan results
    """
    validator = get_validator()

    try:
        validator.validate_target(url)

        cmd = [
            "sqlmap",
            "-u", url,
            "--batch",  # Never ask for user input
            "--level", str(level),
            "--risk", str(risk),
            "--output-dir", "/tmp/sqlmap"
        ]

        if data:
            cmd.extend(["--data", data])

        if cookie:
            cmd.extend(["--cookie", cookie])

        validator.log_tool_execution(
            "sqlmap",
            url,
            {"data": data, "cookie": cookie, "level": level, "risk": risk}
        )

        result = await execute_command(cmd, timeout=900, tool_name="sqlmap")

        return {
            "tool": "sqlmap",
            "target": url,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"SQLMap error: {e}")
        return {
            "tool": "sqlmap",
            "target": url,
            "success": False,
            "error": str(e)
        }


async def wpscan_scan(
    url: str,
    enumerate: str = "vp,vt,u",
    api_token: str = ""
) -> Dict[str, Any]:
    """
    WordPress security scanner.

    Args:
        url: Target WordPress URL
        enumerate: What to enumerate (vp=vulnerable plugins, vt=vulnerable themes, u=users)
        api_token: WPScan API token for vulnerability data

    Returns:
        WordPress scan results
    """
    validator = get_validator()

    try:
        validator.validate_target(url)

        cmd = [
            "wpscan",
            "--url", url,
            "--enumerate", enumerate,
            "--format", "json"
        ]

        if api_token:
            cmd.extend(["--api-token", api_token])

        validator.log_tool_execution(
            "wpscan",
            url,
            {"enumerate": enumerate}
        )

        result = await execute_command(cmd, timeout=600, tool_name="wpscan")

        return {
            "tool": "wpscan",
            "target": url,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"WPScan error: {e}")
        return {
            "tool": "wpscan",
            "target": url,
            "success": False,
            "error": str(e)
        }


async def ffuf_scan(
    url: str,
    wordlist: str = "/usr/share/dirb/wordlists/common.txt",
    extensions: str = "",
    match_codes: str = "200,204,301,302,307,401,403"
) -> Dict[str, Any]:
    """
    Fast web fuzzer.

    Args:
        url: Target URL with FUZZ keyword (e.g., "http://example.com/FUZZ")
        wordlist: Path to wordlist
        extensions: File extensions to fuzz
        match_codes: HTTP status codes to match

    Returns:
        Fuzzing results
    """
    validator = get_validator()

    try:
        # Extract base URL for validation
        base_url = url.replace("FUZZ", "")
        validator.validate_target(base_url)

        cmd = [
            "ffuf",
            "-u", url,
            "-w", wordlist,
            "-mc", match_codes,
            "-of", "json",
            "-o", "/tmp/ffuf_output.json"
        ]

        if extensions:
            cmd.extend(["-e", extensions])

        validator.log_tool_execution(
            "ffuf",
            url,
            {"wordlist": wordlist, "extensions": extensions}
        )

        result = await execute_command(cmd, timeout=600, tool_name="ffuf")

        # Read JSON output if available
        output = result["stdout"]
        try:
            with open("/tmp/ffuf_output.json", "r") as f:
                output = f.read()
        except:
            pass

        return {
            "tool": "ffuf",
            "target": url,
            "success": result["success"],
            "output": output,
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"FFUF error: {e}")
        return {
            "tool": "ffuf",
            "target": url,
            "success": False,
            "error": str(e)
        }


async def httpx_scan(
    target: str,
    follow_redirects: bool = True,
    tech_detect: bool = True
) -> Dict[str, Any]:
    """
    Fast HTTP toolkit for probing and analysis.

    Args:
        target: Target URL, domain, or file with targets
        follow_redirects: Follow HTTP redirects
        tech_detect: Detect web technologies

    Returns:
        HTTP probe results
    """
    validator = get_validator()

    try:
        validator.validate_target(target)

        cmd = [
            "httpx",
            "-u", target,
            "-json"
        ]

        if follow_redirects:
            cmd.append("-follow-redirects")

        if tech_detect:
            cmd.append("-tech-detect")

        validator.log_tool_execution(
            "httpx",
            target,
            {"follow_redirects": follow_redirects, "tech_detect": tech_detect}
        )

        result = await execute_command(cmd, timeout=300, tool_name="httpx")

        return {
            "tool": "httpx",
            "target": target,
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"HTTPX error: {e}")
        return {
            "tool": "httpx",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def wafw00f_scan(
    url: str
) -> Dict[str, Any]:
    """
    Web Application Firewall detection.

    Args:
        url: Target URL

    Returns:
        WAF detection results
    """
    validator = get_validator()

    try:
        validator.validate_target(url)

        cmd = ["wafw00f", url, "-o", "/tmp/wafw00f.json"]

        validator.log_tool_execution("wafw00f", url, {})

        result = await execute_command(cmd, timeout=120, tool_name="wafw00f")

        # Try to read JSON output
        output = result["stdout"]
        try:
            with open("/tmp/wafw00f.json", "r") as f:
                output = f.read()
        except:
            pass

        return {
            "tool": "wafw00f",
            "target": url,
            "success": result["success"],
            "output": output,
            "errors": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Wafw00f error: {e}")
        return {
            "tool": "wafw00f",
            "target": url,
            "success": False,
            "error": str(e)
        }


async def gospider_scan(
    target: str,
    depth: int = 1,
    concurrent: int = 5,
    timeout: int = 5,
    include_subs: bool = False,
    other_source: bool = False
) -> Dict[str, Any]:
    """
    Web crawler for discovering URLs and resources.

    Args:
        target: Target URL to crawl
        depth: Maximum crawl depth (default: 1)
        concurrent: Number of concurrent requests (default: 5)
        timeout: Request timeout in seconds (default: 5)
        include_subs: Include subdomains in crawling (default: False)
        other_source: Use third-party sources (Archive, CommonCrawl, etc.) (default: False)

    Returns:
        Discovered URLs and resources
    """
    import json

    validator = get_validator()

    try:
        validator.validate_target(target)

        # Build gospider command - --json outputs to stdout
        cmd = [
            "gospider",
            "-s", target,
            "-d", str(depth),
            "-c", str(concurrent),
            "-t", str(timeout),
            "--json"
        ]

        if include_subs:
            cmd.append("--include-subs")

        if other_source:
            cmd.append("--other-source")

        validator.log_tool_execution(
            "gospider",
            target,
            {
                "depth": depth,
                "concurrent": concurrent,
                "timeout": timeout,
                "include_subs": include_subs,
                "other_source": other_source
            }
        )

        result = await execute_command(cmd, timeout=300, tool_name="gospider")

        # Parse JSON Lines output from stdout
        findings = []
        urls = set()  # Track unique URLs

        # Gospider with --json outputs JSON Lines to stdout
        stdout = result.get("stdout", "")
        for line in stdout.split('\n'):
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    findings.append(data)

                    # Extract URL for unique count
                    if "output" in data:
                        urls.add(data["output"])
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue

        # Categorize findings by type
        categorized = {
            "urls": [f for f in findings if f.get("type") == "url"],
            "forms": [f for f in findings if f.get("type") == "form"],
            "subdomains": [f for f in findings if f.get("type") == "subdomain"],
            "js": [f for f in findings if f.get("type") == "javascript"],
            "aws": [f for f in findings if f.get("type") == "aws"],
            "linkfinder": [f for f in findings if f.get("type") == "linkfinder"],
            "other": [f for f in findings if f.get("type") not in ["url", "form", "subdomain", "javascript", "aws", "linkfinder"]]
        }

        return {
            "tool": "gospider",
            "target": target,
            "success": result["success"],
            "findings": findings,
            "findings_count": len(findings),
            "unique_urls": len(urls),
            "categorized": {
                "urls_count": len(categorized["urls"]),
                "forms_count": len(categorized["forms"]),
                "subdomains_count": len(categorized["subdomains"]),
                "js_count": len(categorized["js"]),
                "aws_count": len(categorized["aws"]),
                "linkfinder_count": len(categorized["linkfinder"]),
                "other_count": len(categorized["other"])
            },
            "scan_info": result["stderr"],
            "duration_seconds": result["duration_seconds"]
        }

    except Exception as e:
        logger.error(f"Gospider error: {e}")
        return {
            "tool": "gospider",
            "target": target,
            "success": False,
            "error": str(e)
        }


async def http_request(
    url: str,
    method: str = "GET",
    headers: str = "",
    body: str = "",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    HTTP client for fetching web content, downloading files, and testing endpoints.

    Args:
        url: Target URL to request
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: JSON string of headers (e.g., '{"Content-Type": "application/json"}')
        body: Request body for POST/PUT requests
        timeout: Request timeout in seconds

    Returns:
        HTTP response with status, headers, and content
    """
    validator = get_validator()

    try:
        validator.validate_target(url)

        import aiohttp
        import json as json_lib

        # Parse headers if provided
        request_headers = {}
        if headers:
            try:
                request_headers = json_lib.loads(headers)
            except json_lib.JSONDecodeError:
                logger.warning(f"Invalid headers JSON: {headers}")

        validator.log_tool_execution(
            "http_request",
            url,
            {"method": method, "headers": request_headers}
        )

        # Make HTTP request
        async with aiohttp.ClientSession() as session:
            request_kwargs = {
                "headers": request_headers,
                "timeout": aiohttp.ClientTimeout(total=timeout),
                "ssl": False  # Allow self-signed certs for testing
            }

            if body and method.upper() in ["POST", "PUT", "PATCH"]:
                request_kwargs["data"] = body

            start_time = datetime.now()

            async with session.request(method.upper(), url, **request_kwargs) as response:
                # Read response
                content = await response.text()

                # Get response headers
                response_headers = dict(response.headers)

                duration = (datetime.now() - start_time).total_seconds()

                # Detect content type
                content_type = response_headers.get("Content-Type", "").lower()
                is_json = "application/json" in content_type
                is_javascript = any(x in content_type for x in ["javascript", "ecmascript"])
                is_html = "text/html" in content_type

                # Try to parse JSON if applicable
                parsed_content = None
                if is_json:
                    try:
                        parsed_content = json_lib.loads(content)
                    except json_lib.JSONDecodeError:
                        pass

                return {
                    "tool": "http_request",
                    "url": url,
                    "method": method.upper(),
                    "success": True,
                    "status_code": response.status,
                    "status_text": response.reason,
                    "headers": response_headers,
                    "content": content[:50000],  # Limit to 50KB for safety
                    "content_length": len(content),
                    "content_type": content_type,
                    "is_json": is_json,
                    "is_javascript": is_javascript,
                    "is_html": is_html,
                    "parsed_json": parsed_content,
                    "duration_seconds": duration
                }

    except aiohttp.ClientError as e:
        logger.error(f"HTTP request error: {e}")
        return {
            "tool": "http_request",
            "url": url,
            "method": method.upper(),
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        logger.error(f"HTTP request error: {e}")
        return {
            "tool": "http_request",
            "url": url,
            "method": method.upper(),
            "success": False,
            "error": str(e)
        }


# MCP Tool definitions

def list_tools() -> List[types.Tool]:
    """List all web security tools."""
    return [
        types.Tool(
            name="gobuster_scan",
            description="Directory and file brute-forcing tool. Discovers hidden paths and files on web servers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL"
                    },
                    "wordlist": {
                        "type": "string",
                        "description": "Path to wordlist file",
                        "default": "/usr/share/wordlists/dirb/common.txt"
                    },
                    "extensions": {
                        "type": "string",
                        "description": "File extensions (e.g., 'php,html,txt')",
                        "default": ""
                    },
                    "threads": {
                        "type": "integer",
                        "description": "Number of concurrent threads",
                        "default": 10
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="nikto_scan",
            description="Web server vulnerability scanner. Tests for outdated versions, dangerous files, and misconfigurations. Automatically handles HTTP/HTTPS based on URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL (e.g., https://example.com or http://example.com)"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="sqlmap_scan",
            description="Automated SQL injection detection and exploitation tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL"
                    },
                    "data": {
                        "type": "string",
                        "description": "POST data",
                        "default": ""
                    },
                    "cookie": {
                        "type": "string",
                        "description": "HTTP Cookie header value",
                        "default": ""
                    },
                    "level": {
                        "type": "integer",
                        "description": "Level of tests (1-5)",
                        "default": 1
                    },
                    "risk": {
                        "type": "integer",
                        "description": "Risk of tests (1-3)",
                        "default": 1
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="wpscan_scan",
            description="WordPress security scanner. Enumerates plugins, themes, users, and checks for vulnerabilities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target WordPress URL"
                    },
                    "enumerate": {
                        "type": "string",
                        "description": "What to enumerate (vp=vulnerable plugins, vt=vulnerable themes, u=users)",
                        "default": "vp,vt,u"
                    },
                    "api_token": {
                        "type": "string",
                        "description": "WPScan API token",
                        "default": ""
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="ffuf_scan",
            description="Fast web fuzzer for discovering directories, files, and parameters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL with FUZZ keyword (e.g., 'http://example.com/FUZZ')"
                    },
                    "wordlist": {
                        "type": "string",
                        "description": "Path to wordlist",
                        "default": "/usr/share/wordlists/dirb/common.txt"
                    },
                    "extensions": {
                        "type": "string",
                        "description": "File extensions to fuzz",
                        "default": ""
                    },
                    "match_codes": {
                        "type": "string",
                        "description": "HTTP status codes to match",
                        "default": "200,204,301,302,307,401,403"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="httpx_scan",
            description="Fast HTTP toolkit for probing, analyzing, and fingerprinting web servers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL or domain"
                    },
                    "follow_redirects": {
                        "type": "boolean",
                        "description": "Follow HTTP redirects",
                        "default": True
                    },
                    "tech_detect": {
                        "type": "boolean",
                        "description": "Detect web technologies",
                        "default": True
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="wafw00f_scan",
            description="Web Application Firewall (WAF) detection tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="gospider_scan",
            description="Fast web crawler for discovering URLs, forms, subdomains, JavaScript files, and AWS S3 buckets. Can integrate with third-party sources like Archive.org and CommonCrawl.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL to crawl"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Maximum crawl depth",
                        "default": 1
                    },
                    "concurrent": {
                        "type": "integer",
                        "description": "Number of concurrent requests",
                        "default": 5
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds",
                        "default": 5
                    },
                    "include_subs": {
                        "type": "boolean",
                        "description": "Include subdomains in crawling",
                        "default": False
                    },
                    "other_source": {
                        "type": "boolean",
                        "description": "Use third-party sources (Archive.org, CommonCrawl, etc.)",
                        "default": False
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="http_request",
            description="HTTP client for fetching web content, downloading JavaScript files, analyzing API responses, and testing authentication endpoints. Supports GET, POST, PUT, DELETE methods with custom headers and body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL to request"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE, etc.)",
                        "default": "GET"
                    },
                    "headers": {
                        "type": "string",
                        "description": "JSON string of request headers (e.g., '{\"Content-Type\": \"application/json\", \"Authorization\": \"Bearer token\"}')"
                    },
                    "body": {
                        "type": "string",
                        "description": "Request body for POST/PUT requests (raw string or JSON)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Request timeout in seconds",
                        "default": 30
                    }
                },
                "required": ["url"]
            }
        )
    ]


def get_tools() -> List[Dict[str, Any]]:
    """Get tool handlers for registration."""
    return [
        {"name": "gobuster_scan", "handler": gobuster_scan},
        {"name": "nikto_scan", "handler": nikto_scan},
        {"name": "sqlmap_scan", "handler": sqlmap_scan},
        {"name": "wpscan_scan", "handler": wpscan_scan},
        {"name": "ffuf_scan", "handler": ffuf_scan},
        {"name": "httpx_scan", "handler": httpx_scan},
        {"name": "wafw00f_scan", "handler": wafw00f_scan},
        {"name": "gospider_scan", "handler": gospider_scan},
        {"name": "http_request", "handler": http_request},
    ]
