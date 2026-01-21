# Attack Surface Intelligence (ASI-MCP)

AI-Powered Attack Surface Intelligence via Model Context Protocol

## Overview

ASI-MCP is an intelligent security assessment platform that provides AI-driven orchestration of industry-standard penetration testing and vulnerability assessment tools through the Model Context Protocol (MCP). By exposing security tools as MCP-compatible services, ASI-MCP enables AI agents to conduct comprehensive security assessments with human-like reasoning and automation.

## Key Features

**Comprehensive Tool Coverage**
- Network reconnaissance and port scanning (nmap, masscan, rustscan)
- Web application vulnerability scanning (nuclei, nikto, sqlmap)
- Directory and file enumeration (gobuster, feroxbuster, ffuf, dirsearch)
- Web application firewall detection (wafw00f)
- Content discovery and crawling (gospider, katana, httpx)
- Authentication testing and credential brute-forcing (hydra)
- Domain reconnaissance (subfinder, theHarvester)
- Binary analysis (strings, radare2, binwalk)

**AI-Native Architecture**
- Model Context Protocol (MCP) integration for seamless AI agent interaction
- Asynchronous job execution for long-running scans
- Real-time status monitoring and progress tracking
- Structured JSON output optimized for AI analysis

**Enterprise Security**
- Target validation and safety controls
- Comprehensive audit logging
- Rate limiting and resource management
- Non-root container execution
- Health monitoring and metrics

**Production-Ready**
- Docker containerization with Kali Linux base
- FastAPI-based REST API
- Persistent job storage
- Built-in validation for all security tools

## Architecture

ASI-MCP is built on a multi-layered architecture:

```
┌─────────────────────────────────────┐
│   AI Agent (Claude, n8n, etc.)     │
└─────────────┬───────────────────────┘
              │ MCP Protocol
┌─────────────▼───────────────────────┐
│      ASI-MCP Server (FastAPI)       │
│  ┌───────────────────────────────┐  │
│  │   Job Management & Queueing   │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Security Tool Orchestration  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Validation & Safety Layer    │  │
│  └───────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│    Security Tools (Kali Linux)      │
│  nmap | nuclei | gobuster | nikto   │
│  sqlmap | hydra | gospider | ...    │
└─────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker
- Docker Compose
- 4GB RAM minimum
- 20GB disk space

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/asi-mcp.git
cd asi-mcp
```

2. Build and start the container:
```bash
docker-compose up -d --build
```

3. Verify the server is running:
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{"status":"healthy","service":"mcp-security-server","version":"1.0.0"}
```

## Usage

### Direct API Access

ASI-MCP exposes a JSON-RPC 2.0 API over HTTP for MCP tool invocation:

**Example: Port Scan**
```bash
curl -X POST http://localhost:3000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "nmap_scan",
      "arguments": {
        "target": "scanme.nmap.org",
        "ports": "80,443",
        "scan_type": "fast"
      }
    }
  }'
```

**Example: Web Vulnerability Scan**
```bash
curl -X POST http://localhost:3000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "nuclei_scan",
      "arguments": {
        "target": "https://example.com",
        "profile": "pentest"
      }
    }
  }'
```

### Asynchronous Scanning

For long-running scans, use the asynchronous job API:

**1. Start a scan job:**
```bash
curl -X POST http://localhost:3000/scan/start \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "nmap_scan",
    "target": "scanme.nmap.org",
    "scan_type": "comprehensive"
  }'
```

Response:
```json
{
  "job_id": "abc123",
  "status": "running",
  "tool": "nmap_scan",
  "target": "scanme.nmap.org"
}
```

**2. Check job status:**
```bash
curl http://localhost:3000/scan/status/abc123
```

**3. Get results:**
```bash
curl http://localhost:3000/scan/results/abc123
```

### AI Agent Integration

ASI-MCP is designed for use with AI agents via MCP:

**Example with n8n:**
```javascript
// Add MCP tool node
{
  "name": "ASI-MCP",
  "type": "mcp",
  "server": "http://localhost:3000",
  "tool": "nmap_scan",
  "arguments": {
    "target": "{{ $json.target }}",
    "ports": "1-1000"
  }
}
```

**Example with Claude Desktop (config.json):**
```json
{
  "mcpServers": {
    "asi-mcp": {
      "url": "http://localhost:3000"
    }
  }
}
```

## Available Tools

### Network Reconnaissance
- **nmap_scan** - Network port scanning and service detection
- **masscan_scan** - High-speed port scanning
- **rustscan_scan** - Fast port scanner with automatic nmap integration

### Web Application Security
- **nuclei_scan** - Vulnerability scanning with 8000+ templates (pentest profile default)
- **nikto_scan** - Web server vulnerability scanner
- **sqlmap_scan** - SQL injection detection and exploitation
- **gobuster_scan** - Directory and file brute-forcing (raft wordlists)
- **feroxbuster_scan** - Fast content discovery
- **ffuf_scan** - Web fuzzing tool
- **dirsearch_scan** - Web path scanner
- **httpx_scan** - HTTP toolkit for probing
- **wafw00f_scan** - Web application firewall detection
- **gospider_scan** - Web crawler for URL and resource discovery
- **katana_scan** - Next-generation web crawler
- **wpscan_scan** - WordPress security scanner
- **http_request** - HTTP client for content fetching and endpoint testing

### Authentication & Credentials
- **hydra_bruteforce** - Network authentication brute-forcing

### Domain Intelligence
- **subfinder_scan** - Subdomain discovery
- **theharvester_scan** - OSINT and information gathering

### Binary Analysis
- **strings_analyze** - Extract readable strings from binaries
- **radare2_analyze** - Binary analysis and reverse engineering
- **binwalk_analyze** - Firmware analysis and extraction

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=3000
LOG_LEVEL=INFO

# Security Settings
ALLOWED_TARGETS=*  # Comma-separated list or * for all
RATE_LIMIT_PER_MINUTE=60

# Job Management
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT_SECONDS=3600
```

### Target Validation

ASI-MCP includes built-in target validation to prevent scanning unauthorized targets:

- Private IP ranges (RFC 1918) are allowed by default
- Public IP scanning requires explicit authorization
- Domain validation with DNS resolution
- Configurable allow/block lists

To customize validation, edit `src/safety.py`.

### Docker Configuration

Modify `docker-compose.yml` to customize:

```yaml
services:
  mcp-security-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./scans:/tmp/scans
    restart: unless-stopped
```

## Tool-Specific Configuration

### Nuclei
- **Default Profile**: pentest (excludes DoS, fuzzing, and OSINT templates)
- **Templates Location**: `/home/mcpuser/nuclei-templates`
- **Auto-update**: Templates update on container build

### Gobuster
- **Default Wordlist**: raft-medium-directories.txt (30,000 entries)
- **Available Wordlists**:
  - raft-small: 20,115 entries
  - raft-medium: 29,999 entries
  - raft-large: 62,281 entries
- **Location**: `/usr/share/seclists/Discovery/Web-Content/`

### Nikto
- **Timeout**: 1800 seconds (30 minutes)
- **Max Scan Time**: 1500 seconds (25 minutes with -maxtime)
- **Output Format**: JSON with stdout fallback

## Development

### Local Development Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server locally:
```bash
python -m uvicorn src.server:app --host 0.0.0.0 --port 3000 --reload
```

3. Run tests:
```bash
pytest tests/
```

### Project Structure

```
asi-mcp/
├── src/
│   ├── server.py           # FastAPI application and MCP server
│   ├── logging_config.py   # Logging configuration
│   ├── safety.py           # Target validation and safety controls
│   └── tools/
│       ├── network.py      # Network scanning tools
│       ├── web.py          # Web application security tools
│       └── binary.py       # Binary analysis tools
├── config/
│   └── logging.yaml        # Logging configuration
├── docs/
│   ├── fixes-2026-01-14.md
│   └── build-verification.md
├── tests/
│   └── test_*.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Adding New Tools

1. Create tool function in appropriate module (`src/tools/`)
2. Add MCP tool definition to `list_tools()`
3. Register handler in `get_tools()`
4. Add target parameter mapping in `src/server.py`
5. Update documentation

Example:
```python
# src/tools/web.py
async def new_tool_scan(target: str) -> Dict[str, Any]:
    """New security tool implementation."""
    validator = get_validator()
    validator.validate_target(target)

    cmd = ["tool-command", target]
    result = await execute_command(cmd, timeout=300, tool_name="new_tool")

    return {
        "tool": "new_tool",
        "target": target,
        "success": result["success"],
        "output": result["stdout"]
    }
```

## Security Considerations

**Warning**: ASI-MCP contains powerful security testing tools. Use responsibly and only against systems you have explicit authorization to test.

### Best Practices

1. **Authorization**: Always obtain written permission before scanning
2. **Scope**: Define and respect engagement boundaries
3. **Rate Limiting**: Configure appropriate limits to avoid service disruption
4. **Logging**: Enable comprehensive audit logs for compliance
5. **Network Isolation**: Run in isolated networks when possible
6. **Target Validation**: Use allowlists for authorized targets

### Legal Notice

Unauthorized security testing may be illegal in your jurisdiction. Users are solely responsible for ensuring compliance with applicable laws and regulations. The authors and contributors of ASI-MCP assume no liability for misuse of this software.

## Performance

### Resource Requirements

**Minimum**:
- 2 CPU cores
- 4GB RAM
- 20GB disk space

**Recommended**:
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ disk space (for scan results)

### Benchmarks

Typical scan times on recommended hardware:
- nmap comprehensive scan (1000 ports): 5-15 minutes
- nuclei pentest profile: 5-10 minutes
- gobuster raft-medium: 2-5 minutes
- nikto scan: 15-25 minutes
- gospider crawl (depth 2): 1-3 minutes

## Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker logs mcp-security-server

# Rebuild without cache
docker-compose down
docker-compose up -d --build --no-cache
```

**Tools not found**
```bash
# Verify tool installation
docker exec mcp-security-server which nmap
docker exec mcp-security-server nuclei -version
```

**Job timeout**
```bash
# Increase timeout in .env
JOB_TIMEOUT_SECONDS=7200

# Restart container
docker-compose restart
```

**Permission denied errors**
```bash
# Check container user
docker exec mcp-security-server whoami

# Verify file permissions
docker exec mcp-security-server ls -la /tmp/scans
```

## Roadmap

- Integration with vulnerability management platforms
- Scheduled scanning capabilities
- Enhanced reporting and visualization
- Support for distributed scanning
- Integration with CI/CD pipelines
- Additional OSINT and reconnaissance tools
- Cloud security assessment capabilities

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-tool`)
3. Commit your changes (`git commit -m 'Add new security tool'`)
4. Push to the branch (`git push origin feature/new-tool`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation
- Ensure all tests pass before submitting PR

## License

MIT License

Copyright (c) 2026 ASI-MCP Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

- GitHub Issues: https://github.com/yourusername/asi-mcp/issues
- Documentation: https://github.com/yourusername/asi-mcp/wiki
- Security Issues: security@yourdomain.com (responsible disclosure)

## Acknowledgments

Built with:
- Model Context Protocol (MCP) by Anthropic
- Kali Linux security tools
- FastAPI web framework
- Docker containerization

Special thanks to the security research community and open-source tool maintainers.

---

**ASI-MCP** - AI-Powered Attack Surface Intelligence
