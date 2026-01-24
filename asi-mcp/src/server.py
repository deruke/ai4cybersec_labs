"""
Main MCP server with SSE endpoint for n8n integration.
"""

import os
import asyncio
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport

from .logging_config import get_logger, get_audit_logger
from .safety import get_validator
from .scan_manager import get_scan_manager, ScanStatus
from .tools import network, web, cloud, binary, exploit

logger = get_logger(__name__)
audit_logger = get_audit_logger()

# Training banner
TRAINING_BANNER = """
╔═══════════════════════════════════════════════════════════╗
║   AUTHORIZED SECURITY TRAINING ENVIRONMENT ONLY           ║
║   All activities are logged and monitored                 ║
║   For educational purposes - Black Hills InfoSec         ║
╚═══════════════════════════════════════════════════════════╝
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(TRAINING_BANNER)
    logger.info("MCP Security Server starting up")

    # Initialize validator
    validator = get_validator()
    logger.info(f"Safety validator initialized")

    yield

    logger.info("MCP Security Server shutting down")


# Create FastAPI app
app = FastAPI(
    title="MCP Security Training Server",
    description="Educational security testing tools for authorized training",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create MCP server instance
mcp_server = Server("security-training-server")


# Register all tools from modules
def register_tools():
    """Register all security tools with the MCP server."""
    # Network tools
    for tool in network.get_tools():
        mcp_server.request_handlers[f"tools/call:{tool['name']}"] = tool['handler']

    # Web tools
    for tool in web.get_tools():
        mcp_server.request_handlers[f"tools/call:{tool['name']}"] = tool['handler']

    # Cloud tools
    for tool in cloud.get_tools():
        mcp_server.request_handlers[f"tools/call:{tool['name']}"] = tool['handler']

    # Binary tools
    for tool in binary.get_tools():
        mcp_server.request_handlers[f"tools/call:{tool['name']}"] = tool['handler']

    # Exploitation tools
    for tool in exploit.get_tools():
        mcp_server.request_handlers[f"tools/call:{tool['name']}"] = tool['handler']

    logger.info("All security tools registered")


# List tools handler
@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available security tools."""
    tools = []

    # Gather tools from all modules
    for module in [network, web, cloud, binary, exploit]:
        tools.extend(module.list_tools())

    logger.info(f"Listed {len(tools)} available tools")
    return tools


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "MCP Security Training Server",
        "version": "1.0.0",
        "description": "Educational security testing tools for authorized training",
        "protocolVersion": "2025-03-26",
        "transport": "streamable-http",
        "endpoints": {
            "mcp": "/messages",
            "sse_legacy": "/sse (deprecated)",
            "health": "/health",
            "tools": "/tools",
            "docs": "/docs"
        },
        "configuration": {
            "n8n": {
                "transport": "HTTP / Streamable HTTP (NOT SSE)",
                "url": "http://mcp-security-server:3000/messages",
                "note": "SSE transport is deprecated. Use Streamable HTTP instead."
            }
        },
        "banner": TRAINING_BANNER
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-security-server",
        "version": "1.0.0"
    }


@app.get("/tools")
async def list_available_tools():
    """
    List all available security tools with descriptions.
    """
    tools = []

    # Gather tools from all modules
    for module in [network, web, cloud, binary, exploit]:
        module_tools = module.list_tools()
        for tool in module_tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })

    audit_logger.info(f"Tools listed")

    return {
        "tools": tools,
        "count": len(tools)
    }


@app.get("/sse")
async def handle_sse(request: Request):
    """
    SSE endpoint for n8n MCP Client Tool integration.

    This endpoint handles the Server-Sent Events protocol for MCP communication.
    """
    logger.info(f"SSE connection initiated from {request.client.host}")
    audit_logger.info(f"SSE connection from {request.client.host}")

    from sse_starlette.sse import EventSourceResponse
    import json

    async def event_generator():
        """Generate MCP protocol events."""
        try:
            # Send initialization
            init_message = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mcp-security-server",
                        "version": "1.0.0"
                    }
                }
            }
            yield {"data": json.dumps(init_message)}

            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                yield {"event": "ping", "data": ""}

        except Exception as e:
            logger.error(f"SSE generator error: {e}", exc_info=True)
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
    response = await call_next(request)
    return response


@app.api_route("/messages", methods=["POST", "GET"])
async def handle_messages(
    request: Request
):
    """
    Handle MCP protocol messages via Streamable HTTP transport.

    Supports both POST (client-to-server messages) and GET (optional server-to-client streaming).
    This implements the modern MCP Streamable HTTP transport (protocol version 2025-03-26).
    """
    # Handle GET request for optional streaming
    if request.method == "GET":
        logger.info("GET request to /messages - returning server info")
        return JSONResponse({
            "name": "mcp-security-server",
            "version": "1.0.0",
            "protocolVersion": "2025-03-26",
            "transport": "streamable-http",
            "capabilities": {
                "tools": {}
            }
        })

    # Handle POST request for JSON-RPC messages
    try:
        message = await request.json()
        method = message.get("method")
        msg_id = message.get("id")

        logger.info(f"Received MCP message: {method}")
        logger.debug(f"Full message: {message}")

        # Handle initialization
        if method == "initialize":
            logger.info("MCP initialization request received")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mcp-security-server",
                        "version": "1.0.0"
                    }
                }
            })

        # Handle tool listing
        elif method == "tools/list":
            logger.info("Tool list request received")
            tools = []

            # Gather tools from all modules
            for module in [network, web, cloud, binary, exploit]:
                module_tools = module.list_tools()
                for tool in module_tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })

            logger.info(f"Returning {len(tools)} tools")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": tools
                }
            })

        # Handle tool execution
        elif method == "tools/call":
            tool_name = message.get("params", {}).get("name")
            arguments = message.get("params", {}).get("arguments", {})

            logger.info(f"Tool call: {tool_name} with args: {arguments}")
            audit_logger.info(f"Tool execution: {tool_name} with args {arguments}")

            # Get all tool handlers
            handlers = {}
            for module in [network, web, cloud, binary, exploit]:
                for tool_info in module.get_tools():
                    handlers[tool_info["name"]] = tool_info["handler"]

            if tool_name not in handlers:
                logger.error(f"Unknown tool: {tool_name}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                })

            # Execute the tool
            try:
                # Filter out MCP session/metadata parameters that tools don't need
                # n8n and AI models may add extra parameters for context/reasoning:
                # - sessionId: session tracking
                # - action: AI reasoning about what action it's performing
                # - chatInput: original user message (n8n chat context)
                # - tool: tool name (redundant, we already know it)
                # - toolCallId: n8n's internal tracking ID
                # - output: AI agent's expected output format
                # - _meta, _request, _session: internal MCP metadata
                mcp_reserved_params = {
                    "sessionId", "action", "chatInput", "tool", "toolCallId",
                    "_meta", "_request", "_session", "output"
                }
                filtered_args = {
                    k: v for k, v in arguments.items()
                    if k not in mcp_reserved_params
                }

                if len(arguments) != len(filtered_args):
                    removed = set(arguments.keys()) - set(filtered_args.keys())
                    logger.debug(f"Filtered out MCP params: {removed}")
                logger.debug(f"Calling {tool_name} with args: {filtered_args}")
                result = await handlers[tool_name](**filtered_args)
                result_text = str(result)

                logger.info(f"Tool {tool_name} executed successfully")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
                    }
                })
            except Exception as tool_error:
                logger.error(f"Tool execution error: {tool_error}", exc_info=True)
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(tool_error)}"
                    }
                })

        # Unknown method
        else:
            logger.warning(f"Unknown MCP method: {method}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status_code=500)


# Asynchronous Scan Endpoints
@app.post("/scans/start")
async def start_async_scan(request: Request):
    """
    Start an asynchronous scan job.

    This allows long-running scans (like nuclei) to execute in the background
    without blocking the API request.

    Request body:
    {
        "tool": "nuclei_scan",
        "target": "https://example.com",
        "arguments": {"severity": "high,critical"},
        "webhook_url": "https://optional-callback.com/webhook" (optional)
    }

    Returns:
    {
        "job_id": "uuid",
        "status": "pending",
        "message": "Scan job created"
    }
    """
    try:
        data = await request.json()
        tool_name = data.get("tool")
        target = data.get("target")
        arguments = data.get("arguments", {})
        webhook_url = data.get("webhook_url")

        if not tool_name or not target:
            return JSONResponse({
                "error": "Missing required fields: tool, target"
            }, status_code=400)

        # Get tool handler
        handlers = {}
        for module in [network, web, cloud, binary, exploit]:
            for tool_info in module.get_tools():
                handlers[tool_info["name"]] = tool_info["handler"]

        if tool_name not in handlers:
            return JSONResponse({
                "error": f"Unknown tool: {tool_name}"
            }, status_code=400)

        # Map target to correct parameter name for each tool
        # Different tools use different parameter names (target, url, domain, etc.)
        TOOL_TARGET_PARAMS = {
            # Network tools - use "target"
            "nmap_scan": "target",
            "masscan_scan": "target",
            "rustscan_scan": "target",
            "nuclei_scan": "target",
            "nikto_scan": "target",
            "httpx_scan": "target",
            "hydra_bruteforce": "target",
            "crackmapexec_scan": "target",

            # Web tools - use "url"
            "gobuster_scan": "url",
            "sqlmap_scan": "url",
            "wpscan_scan": "url",
            "ffuf_scan": "url",
            "wafw00f_scan": "url",
            "http_request": "url",
            "gospider_scan": "target",

            # Domain-based tools - use "domain"
            "subfinder_scan": "domain",
            "theharvester_scan": "domain",

            # Binary analysis - use "file_path"
            "strings_analyze": "file_path",
            "binwalk_analyze": "file_path",
            "radare2_analyze": "file_path",

            # Hash cracking - use "hash_file"
            "hashcat_crack": "hash_file",
            "john_crack": "hash_file",

            # Cloud tools - use "provider"
            "prowler_scan": "provider",
            "scoutsuite_scan": "provider"
        }

        target_param = TOOL_TARGET_PARAMS.get(tool_name, "target")
        tool_arguments = {target_param: target}
        tool_arguments.update(arguments)

        # Create scan job
        scan_manager = get_scan_manager()
        job_id = scan_manager.create_job(tool_name, target, tool_arguments, webhook_url)

        # Start job in background
        scan_manager.start_job(job_id, handlers[tool_name])

        audit_logger.info(f"Started async scan job {job_id}: {tool_name} -> {target}")

        return JSONResponse({
            "job_id": job_id,
            "status": "pending",
            "tool": tool_name,
            "target": target,
            "message": "Scan job created and started",
            "status_url": f"/scans/{job_id}/status",
            "results_url": f"/scans/{job_id}/results"
        })

    except Exception as e:
        logger.error(f"Error starting async scan: {e}", exc_info=True)
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


@app.get("/scans/{job_id}/status")
async def get_scan_status(job_id: str):
    """
    Get the status of an async scan job.

    Returns:
    {
        "job_id": "uuid",
        "tool_name": "nuclei_scan",
        "target": "https://example.com",
        "status": "running|completed|failed",
        "created_at": "2026-01-14T12:00:00",
        "started_at": "2026-01-14T12:00:01",
        "completed_at": "2026-01-14T12:05:00",
        "duration_seconds": 299.5
    }
    """
    scan_manager = get_scan_manager()
    status = scan_manager.get_job_status(job_id)

    if not status:
        return JSONResponse({
            "error": f"Job {job_id} not found"
        }, status_code=404)

    return JSONResponse(status)


@app.get("/scans/{job_id}/results")
async def get_scan_results(job_id: str):
    """
    Get the results of a completed scan job.

    Returns the full scan results if the job is completed,
    otherwise returns the current status.
    """
    scan_manager = get_scan_manager()
    results = scan_manager.get_job_results(job_id)

    if not results:
        return JSONResponse({
            "error": f"Job {job_id} not found"
        }, status_code=404)

    return JSONResponse(results)


@app.get("/scans")
async def list_scans(
    status: Optional[str] = None,
    tool: Optional[str] = None,
    limit: int = 50
):
    """
    List scan jobs with optional filters.

    Query parameters:
    - status: Filter by status (pending, running, completed, failed, cancelled)
    - tool: Filter by tool name
    - limit: Maximum number of results (default 50)
    """
    scan_manager = get_scan_manager()

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = ScanStatus(status.lower())
        except ValueError:
            return JSONResponse({
                "error": f"Invalid status: {status}. Valid values: "
                        f"{', '.join([s.value for s in ScanStatus])}"
            }, status_code=400)

    jobs = scan_manager.list_jobs(
        status=status_filter,
        tool_name=tool,
        limit=limit
    )

    return JSONResponse({
        "jobs": jobs,
        "count": len(jobs)
    })


@app.post("/scans/{job_id}/cancel")
async def cancel_scan(job_id: str):
    """
    Cancel a running scan job.

    Only works for pending or running jobs.
    """
    scan_manager = get_scan_manager()
    success = scan_manager.cancel_job(job_id)

    if not success:
        return JSONResponse({
            "error": f"Job {job_id} cannot be cancelled (not found or already completed)"
        }, status_code=400)

    audit_logger.info(f"Cancelled scan job {job_id}")

    return JSONResponse({
        "job_id": job_id,
        "message": "Job cancelled successfully"
    })


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred"
        }
    )


# Initialize tools on startup
register_tools()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 3000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None  # Use our custom logging
    )
