# AI4CyberSec Labs

An Open WebUI-based Capture The Flag (CTF) environment focused on LLM prompt injection challenges. This project provides a complete training environment for learning about AI security, prompt injection attacks, and defensive techniques.

## Overview

This environment consists of multiple Docker containers orchestrating a CTF platform with 5 different security challenges, plus integrated tools for workflow automation and security testing:

- **Open WebUI**: Web interface hosting the CTF challenge models
- **Ollama**: Local LLM server running Llama 3.1:8b
- **Pipelines**: ML-based prompt filtering using LLM Guard
- **n8n**: Workflow automation platform
- **ASI-MCP**: Attack Surface Intelligence server providing security tools via MCP protocol
- **PostgreSQL**: Database backend for n8n
- **Jupyter**: Notebook environment for student exercises

## CTF Challenges

Each challenge presents a different defensive configuration that participants must bypass to extract a secret flag:

| Challenge | Defense Mechanism | Description |
|-----------|------------------|-------------|
| 1 | None | Basic prompt injection with no protections |
| 2 | System Prompt | Anti-injection instructions in the system prompt |
| 3 | Input Filter | Keyword-based input filtering |
| 4 | Output Filter | Pattern-based output filtering |
| 5 | LLM Prompt Guard | ML-based prompt injection detection |

All challenges feature "Dr. Daniel Jackson" from Stargate SG-1 as the character persona, with flags hidden in the system prompts.

## Prerequisites

- Docker and Docker Compose
- 16GB+ RAM recommended
- 20GB+ free disk space
- Linux, macOS, or Windows with WSL2

### Optional

- NVIDIA GPU with CUDA support (Linux/WSL2 only)
- NVIDIA Container Toolkit for GPU acceleration

## Quick Start

### Automated Setup

```bash
# Full setup (installs prerequisites if needed)
./setup.sh --all --non-interactive

# Setup CTF environment only (Docker must be installed)
./setup.sh --ctf

# Install prerequisites only
./setup.sh --prerequisites
```

### Manual Setup

```bash
# Build and start all services
docker compose build
docker compose up -d

# Run CTF configuration
docker compose run --rm ctf-setup

# View logs
docker compose logs -f
```

## Accessing Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Open WebUI | http://localhost:4242 | admin@ctf.local / ctf_admin_password |
| Jupyter | http://localhost:8888 | Token: AntiSyphonBlackHillsTrainingFtw! |
| n8n | http://localhost:5678 | Create account on first access |
| ASI-MCP | http://localhost:3000 | API token in .env |
| Ollama API | http://localhost:11434 | No auth required |
| PostgreSQL | localhost:5432 | n8n / n8n_password |

Default credentials can be changed in the `.env` file.

## Configuration

All configuration is managed through the `.env` file:

```bash
# Ports
OPENWEBUI_PORT=4242
JUPYTER_PORT=8888
N8N_PORT=5678
MCP_PORT=3000
POSTGRES_PORT=5432

# CTF Flags (change these for your deployment)
CTF_FLAG_CHALLENGE_1=YourFlag1
CTF_FLAG_CHALLENGE_2=YourFlag2
CTF_FLAG_CHALLENGE_3=YourFlag3
CTF_FLAG_CHALLENGE_4=YourFlag4
CTF_FLAG_CHALLENGE_5=YourFlag5

# Credentials
CTF_ADMIN_EMAIL=admin@ctf.local
CTF_ADMIN_PASSWORD=ctf_admin_password
CTF_USER_EMAIL=ctf@ctf.local
CTF_USER_PASSWORD=Hellollmworld!
```

## Architecture

```
                    +-------------------+
                    |    Open WebUI     |
                    |   (CTF Interface) |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v----+  +------v------+  +----v--------+
     |   Ollama    |  |  Pipelines  |  |  ctf-setup  |
     | (LLM Server)|  |(LLM Guard)  |  | (Config)    |
     +-------------+  +-------------+  +-------------+

     +-------------+  +-------------+  +-------------+
     |    n8n      |  |   ASI-MCP   |  |   Jupyter   |
     | (Workflows) |  | (Sec Tools) |  | (Notebooks) |
     +------+------+  +-------------+  +-------------+
            |
     +------v------+
     | PostgreSQL  |
     +-------------+
```

All services communicate over a shared Docker network.

## Project Structure

```
ai4cybersec_labs/
├── docker-compose.yaml      # Main service definitions
├── setup.sh                 # Automated setup script
├── .env                     # Configuration variables
├── CLAUDE.md               # AI assistant instructions
├── openwebui/
│   ├── ctf_config.json.template  # Challenge definitions
│   ├── setup.py                  # Open WebUI API automation
│   ├── functions/                # Filter implementations
│   │   ├── input_filter.py
│   │   ├── output_filter.py.template
│   │   └── flag_check_filter.py.template
│   └── pipelines/
│       └── prompt_guard.py       # LLM Guard pipeline
├── asi-msp/                      # ASI-MCP security server
│   ├── src/
│   │   ├── server.py
│   │   ├── safety.py
│   │   └── tools/
│   └── tests/
├── Dockerfile.jupyter
├── Dockerfile.ollama
├── Dockerfile.openwebui
└── Dockerfile.ctfsetup
```

## Development

### Modifying Challenges

1. Edit `openwebui/ctf_config.json.template` to change challenge configurations
2. Modify filter files in `openwebui/functions/`
3. Rebuild and re-run setup:

```bash
docker compose build ctf-setup
docker compose run --rm ctf-setup
```

### Changing Flags

1. Edit flag values in `.env`
2. Restart the environment:

```bash
docker compose down
docker compose up -d
docker compose run --rm ctf-setup
```

### Debugging

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f open-webui
docker compose logs -f ctf-setup

# Access container shell
docker exec -it open-webui bash
docker exec -it mcp-security-server bash

# Check service status
docker compose ps
```

### Reset Environment

```bash
# Remove all containers, volumes, and networks
docker compose down -v

# Rebuild and start fresh
docker compose build
docker compose up -d
```

## n8n Integration

n8n can communicate with other services for workflow automation:

- Ollama API: `http://ollama:11434`
- ASI-MCP API: `http://mcp-security-server:3000`
- Open WebUI API: `http://open-webui:8080`

Data persists in the PostgreSQL database and n8n_data volume.

## ASI-MCP Security Server

The ASI-MCP server provides security scanning tools via JSON-RPC 2.0:

```bash
# Health check
curl http://localhost:3000/health

# Available endpoints
POST /messages     # MCP tool invocation
POST /scan/start   # Start async scan
GET /scan/status/{job_id}
GET /scan/results/{job_id}
```

Available tools include nmap, nuclei, gobuster, sqlmap, nikto, hydra, and more.

## Platform Support

| Platform | GPU Support | Notes |
|----------|-------------|-------|
| Linux (Ubuntu/Debian) | Yes | Full NVIDIA GPU acceleration |
| macOS | No | CPU-only mode |
| Windows WSL2 | Yes | Requires Windows GPU drivers |

GPU support is automatically detected by setup.sh and configured via docker-compose.override.yml.

## Troubleshooting

### Services not starting

```bash
# Check container status
docker compose ps

# View logs for errors
docker compose logs -f

# Ensure ports are not in use
lsof -i :4242
lsof -i :5678
```

### CTF setup fails

```bash
# Wait for Open WebUI to be fully ready
docker compose logs -f open-webui

# Re-run setup after services are healthy
docker compose run --rm ctf-setup
```

### n8n file access errors

n8n v2.0+ has strict file access permissions. The `N8N_RESTRICT_FILE_ACCESS_TO` environment variable in docker-compose.yaml controls allowed directories.

### GPU not detected

```bash
# Verify NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## License

This project is provided for educational purposes.

## Acknowledgments

- Open WebUI project
- Ollama
- LLM Guard
- n8n
- Stargate SG-1 (character inspiration)
