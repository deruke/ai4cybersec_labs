# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Open WebUI-based CTF (Capture The Flag) environment focused on LLM prompt injection challenges. The system consists of multiple Docker containers orchestrating a complete challenge environment with 5 different security challenges, plus an integrated ASI-MCP (Attack Surface Intelligence) server for AI-powered penetration testing automation via the Model Context Protocol.

## Architecture

### Docker Services

The application uses Docker Compose with 8 main services:

- **ollama** (port 11434): LLM model server running Llama 3.1:8b
- **open-webui** (port 4242/4343): Main CTF interface exposing challenge models
- **pipelines** (port 9099): Custom processing pipelines for prompt filtering
- **jupyter** (port 8888): Code execution environment (available for future challenges)
- **postgres** (port 5432): PostgreSQL database for n8n workflow/credential storage
- **n8n** (port 5678): Workflow automation platform with access to ollama and other services
- **mcp-security-server** (port 3000): ASI-MCP server for AI-powered security testing via MCP
- **ctf-setup**: One-time setup container that configures the CTF via API calls

All services are on the same Docker network and can communicate using service names (e.g., n8n can access ollama at `http://ollama:11434`). The mcp-security-server provides MCP (Model Context Protocol) endpoints for AI agents to perform automated security testing.

### Key Components

**CTF Configuration**: `openwebui/ctf_config.json.template`
- Defines all 5 challenge models with their system prompts
- Configures functions (filters) and pipelines
- Uses environment variable placeholders (e.g., `${CTF_FLAG_CHALLENGE_1}`)
- Template is processed by setup.py to substitute flags and settings

**Setup Automation**: `openwebui/setup.py`
- Python script that configures Open WebUI via REST API
- Creates users, models, functions, and pipelines
- Handles authentication and model associations
- Uses retry logic for reliability

**Challenge Components**:
- Functions (filters): `openwebui/functions/` - Python filters for input/output validation (`.template` files have flag placeholders substituted at setup time)
- Pipelines: `openwebui/pipelines/` - ML-based prompt guard for Challenge 5

### Template System

Files ending in `.template` contain flag placeholders that are replaced during setup:
- System prompts in `ctf_config.json.template` use `{flag:${CTF_FLAG_CHALLENGE_X}}`
- Filter files use direct environment variable substitution `${CTF_FLAG_CHALLENGE_X}`
- The ctf-setup container receives all flags as environment variables

### Challenge Architecture

Each challenge is a separate model in Open WebUI with different security configurations:

1. **Challenge 1**: No protections - basic prompt injection
2. **Challenge 2**: System prompt with anti-injection instructions
3. **Challenge 3**: Input filtering via `input_filter.py`
4. **Challenge 4**: Output filtering via `output_filter.py`
5. **Challenge 5**: ML-based prompt guard pipeline

Models are configured with `filter_ids` to associate filter functions.

### ASI-MCP Server

**Location**: `asi-msp/` directory (Attack Surface Intelligence via MCP)

The ASI-MCP component is an AI-powered penetration testing framework providing JSON-RPC 2.0 tool invocation:
- Comprehensive security tools (nmap, nuclei, gobuster, sqlmap, nikto, hydra, etc.)
- Kali Linux base image with security tools pre-installed
- MCP (Model Context Protocol) integration for AI agent communication
- Asynchronous job execution for long-running scans
- Target validation and safety controls
- Non-root container execution with NET_ADMIN/NET_RAW capabilities

**Key Files**:
- `src/server.py` - FastAPI application and MCP endpoint handlers
- `src/safety.py` - Target validation and safety controls
- `src/tools/` - Tool implementations (network.py, web.py, binary.py, cloud.py, exploit.py)
- `tests/` - pytest test suite

**Docker Integration**:
- Runs in isolated container with security tools pre-installed
- Logs mounted at `./asi-msp/logs`
- Config mounted at `./asi-msp/config`
- Scan results stored in `scan-results` Docker volume at `/tmp/scans`
- Resource limits: 4GB memory max, 4 CPUs max, 2GB minimum

**n8n Integration**:
- n8n can read ASI-MCP logs from `/asi-mcp-logs` volume (read-only)
- Full ASI-MCP directory available at `/asi-mcp` (read-only)
- Can be used for automated security testing workflows

## Common Development Tasks

### Building and Running

```bash
# Full automated setup (Linux/Mac with prerequisites)
./setup.sh --all --non-interactive

# Install prerequisites only (Docker, NVIDIA drivers on Linux)
./setup.sh --prerequisites

# Setup CTF environment only
./setup.sh --ctf

# Manual Docker commands
docker compose build
docker compose up -d
docker compose down -v  # Reset everything
```

### Modifying Challenges

**Changing Flags**: Edit `.env` file, then restart:
```bash
docker compose down
docker compose up -d
```

**Modifying System Prompts**: Edit `openwebui/ctf_config.json.template`, then:
```bash
docker compose run --rm ctf-setup
```

**Updating Filters**: Modify files in `openwebui/functions/`, then re-run setup:
```bash
docker compose run --rm ctf-setup
```

### Debugging

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f open-webui
docker compose logs -f ctf-setup
docker compose logs -f n8n

# Check service status
docker compose ps

# Access container shell
docker exec -it open-webui bash
docker exec -it ollama bash
docker exec -it jupyter bash
docker exec -it n8n sh
```

### Using n8n with Ollama

n8n can communicate with ollama for workflow automation:
- Ollama API endpoint from n8n: `http://ollama:11434`
- n8n web interface: http://localhost:5678
- Data persists in the `n8n_data` volume
- See `N8N_SETUP.md` for detailed integration guide

**Important**: n8n v2.0+ (2025) has strict file access permissions due to critical RCE vulnerability fixes (CVE-2025-68613, CVE-2026-21858). The `N8N_RESTRICT_FILE_ACCESS_TO` environment variable in docker-compose.yaml allows n8n to read from `/asi-mcp-logs;/asi-mcp;/home/node/.n8n-files` directories (semicolon-separated). If you encounter "Access to the file is not allowed" errors, see `N8N_FILE_ACCESS_FIX.md`.

### ASI-MCP Operations

```bash
# View ASI-MCP logs
docker compose logs -f mcp-security-server

# Access ASI-MCP container shell
docker exec -it mcp-security-server bash

# Test ASI-MCP API health
curl http://localhost:3000/health

# View scan logs
ls -la asi-msp/logs/
```

### Testing Changes

After modifying challenge configuration:
1. Rebuild the ctf-setup image: `docker compose build ctf-setup`
2. Re-run setup: `docker compose run --rm ctf-setup`
3. Verify in Open WebUI at http://localhost:4242

### ASI-MCP Testing

```bash
# Run ASI-MCP test suite (inside container or with local Python)
cd asi-msp
pytest tests/

# Run specific test file
pytest tests/test_safety.py

# Run with verbose output
pytest tests/ -v
```

## Platform Support

- **Linux** (Ubuntu/Debian): Full support with optional NVIDIA GPU acceleration
- **macOS**: CPU-only mode (no GPU passthrough support)
- **WSL2**: GPU support via Windows host drivers

GPU configuration is controlled by `docker-compose.override.yml` (auto-generated by setup.sh).

## Important File Locations

### CTF Container Locations
- Setup script working directory: `/app/openwebui` in ctf-setup container
- Open WebUI data volume: Persists user data, chat history, and configurations

### ASI-MCP Locations
- Server working directory: `/app` in mcp-security-server container
- Security tools: Kali Linux tools at standard paths
- Wordlists: `/usr/share/seclists/` (SecLists collection)
- Logs directory (host): `./asi-msp/logs/`
- Config directory (host): `./asi-msp/config/`
- Scan results: Docker volume `scan-results` mounted at `/tmp/scans`

### Docker Volumes
- `ollama` - Ollama model storage
- `open-webui` - Open WebUI application data
- `pipelines` - Pipeline configurations
- `jupyter-work` - Jupyter notebooks and workspace
- `postgres_data` - PostgreSQL database files for n8n
- `n8n_data` - n8n local files and encryption keys
- `scan-results` - ASI-MCP scan results

## API Integration

### Open WebUI API

The setup.py script demonstrates the Open WebUI API workflow:
1. Authenticate via `/api/v1/auths/signup` or `/api/v1/auths/signin`
2. Create functions via `/api/v1/functions/create`
3. Create models via `/api/v1/models/create`
4. Upload pipelines via `/api/v1/pipelines/upload`
5. Configure pipeline valves via `/api/v1/pipelines/{id}/valves/update`

All API calls use Bearer token authentication obtained during login.

### ASI-MCP API

The ASI-MCP server exposes JSON-RPC 2.0 endpoints at `http://localhost:3000`:
- `/health` - Server health check
- `/messages` - MCP tool invocation (JSON-RPC 2.0)
- `/scan/start` - Start async scan job
- `/scan/status/{job_id}` - Check job status
- `/scan/results/{job_id}` - Get scan results

**Available Security Tools**:
- Network: nmap, masscan, rustscan
- Web: nuclei, nikto, sqlmap, gobuster, feroxbuster, ffuf, dirsearch, httpx, wafw00f, gospider, katana, wpscan
- Auth: hydra
- Domain: subfinder, theharvester
- Binary: strings, radare2, binwalk

## Environment Variables

All configuration is managed through the `.env` file:
- **Port Configuration**: OPENWEBUI_PORT, JUPYTER_PORT, N8N_PORT, MCP_PORT, POSTGRES_PORT
- **Authentication**: CTF_ADMIN_EMAIL, CTF_ADMIN_PASSWORD, CTF_USER_EMAIL, CTF_USER_PASSWORD
- **Service URLs**: OPENWEBUI_URL, N8N_WEBHOOK_URL
- **CTF Flags**: CTF_FLAG_CHALLENGE_1 through CTF_FLAG_CHALLENGE_5
- **GPU Support**: ENABLE_GPU (controls docker-compose.override.yml generation)
- **Tokens**: JUPYTER_TOKEN for Jupyter notebook access, MCP_TOKEN for ASI-MCP authentication
- **PostgreSQL**: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB (used by n8n for persistent storage)
- **ASI-MCP Config**: LOG_LEVEL, AUTHORIZED_NETWORKS, BLACKLISTED_NETWORKS, AUTHORIZED_DOMAINS, DEBUG
