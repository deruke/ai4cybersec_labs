.PHONY: help build up down restart logs test clean setup

help:
	@echo "MCP Security Training Server - Make Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup     - Initial setup (copy .env, generate token)"
	@echo "  make build     - Build Docker image"
	@echo ""
	@echo "Runtime Commands:"
	@echo "  make up        - Start server"
	@echo "  make down      - Stop server"
	@echo "  make restart   - Restart server"
	@echo "  make logs      - View logs"
	@echo ""
	@echo "Development Commands:"
	@echo "  make test      - Run tests"
	@echo "  make shell     - Open shell in container"
	@echo "  make clean     - Clean up containers and volumes"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make health    - Check server health"
	@echo "  make tools     - List available tools"
	@echo "  make audit     - View audit logs"

setup:
	@echo "Setting up MCP Security Server..."
	@cp .env.example .env
	@echo "MCP_TOKEN=$$(openssl rand -base64 32)" >> .env
	@echo "✓ Created .env file with secure token"
	@mkdir -p logs config/wordlists
	@echo "✓ Created directories"
	@echo ""
	@echo "Setup complete! Edit .env to customize settings."
	@echo "Run 'make build' to build the Docker image."

build:
	@echo "Building Docker image..."
	docker-compose build
	@echo "✓ Build complete"

up:
	@echo "Starting MCP Security Server..."
	docker-compose up -d
	@echo "✓ Server started"
	@echo "Run 'make health' to verify"

down:
	@echo "Stopping MCP Security Server..."
	docker-compose down
	@echo "✓ Server stopped"

restart:
	@echo "Restarting MCP Security Server..."
	docker-compose restart
	@echo "✓ Server restarted"

logs:
	docker-compose logs -f

test:
	@echo "Running tests..."
	docker exec mcp-security-server pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	docker exec mcp-security-server pytest tests/ --cov=src --cov-report=html
	@echo "✓ Coverage report generated in htmlcov/"

shell:
	docker exec -it mcp-security-server /bin/bash

health:
	@echo "Checking server health..."
	@curl -s http://localhost:3000/health | python3 -m json.tool

tools:
	@echo "Listing available tools..."
	@curl -s -H "Authorization: Bearer $$(grep MCP_TOKEN .env | cut -d '=' -f2)" \
		http://localhost:3000/tools | python3 -m json.tool

audit:
	@echo "Viewing audit logs..."
	docker exec mcp-security-server tail -f /app/logs/audit.log

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@rm -rf logs/*.log
	@echo "✓ Cleanup complete"

clean-all: clean
	@echo "Removing Docker images..."
	docker-compose down --rmi all
	@echo "✓ Full cleanup complete"

# Development helpers
dev-rebuild:
	@echo "Rebuilding without cache..."
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✓ Rebuild complete"

dev-logs-server:
	docker exec mcp-security-server tail -f /app/logs/server.log

dev-logs-audit:
	docker exec mcp-security-server tail -f /app/logs/audit.log

# Quick test commands
test-nmap:
	@echo "Testing nmap scan..."
	@curl -X POST http://localhost:3000/messages \
		-H "Authorization: Bearer $$(grep MCP_TOKEN .env | cut -d '=' -f2)" \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"nmap_scan","arguments":{"target":"192.168.1.1","ports":"80,443"}}}' \
		| python3 -m json.tool

test-httpx:
	@echo "Testing httpx scan..."
	@curl -X POST http://localhost:3000/messages \
		-H "Authorization: Bearer $$(grep MCP_TOKEN .env | cut -d '=' -f2)" \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"httpx_scan","arguments":{"target":"http://192.168.1.1"}}}' \
		| python3 -m json.tool
