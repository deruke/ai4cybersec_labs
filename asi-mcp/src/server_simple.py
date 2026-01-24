"""
Simplified MCP server for n8n integration - without authentication for testing.
"""

import os
import asyncio
from typing import Any
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

from .logging_config import get_logger
from .tools import network, web, cloud, binary, exploit

logger = get_logger(__name__)

# Create MCP server instance
mcp_server = Server("security-training-server")


# Register list_tools handler
@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available security tools."""
    tools = []

    # Gather tools from all modules
    for module in [network, web, cloud, binary, exploit]:
        tools.extend(module.list_tools())

    logger.info(f"Listed {len(tools)} available tools")
    return tools


# Register tool call handlers
@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a security tool."""
    logger.info(f"Tool call: {name} with args {arguments}")

    # Map tool names to handlers
    tool_handlers = {}

    # Network tools
    for tool_info in network.get_tools():
        tool_handlers[tool_info["name"]] = tool_info["handler"]

    # Web tools
    for tool_info in web.get_tools():
        tool_handlers[tool_info["name"]] = tool_info["handler"]

    # Cloud tools
    for tool_info in cloud.get_tools():
        tool_handlers[tool_info["name"]] = tool_info["handler"]

    # Binary tools
    for tool_info in binary.get_tools():
        tool_handlers[tool_info["name"]] = tool_info["handler"]

    # Exploitation tools
    for tool_info in exploit.get_tools():
        tool_handlers[tool_info["name"]] = tool_info["handler"]

    # Execute tool
    if name not in tool_handlers:
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

    try:
        result = await tool_handlers[name](**arguments)
        result_text = str(result)
        logger.info(f"Tool {name} completed successfully")
        return [types.TextContent(type="text", text=result_text)]
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [types.TextContent(type="text", text=error_msg)]


async def handle_sse(request):
    """Handle SSE connection for MCP protocol."""
    logger.info("SSE connection initiated")

    async with SseServerTransport("/messages") as (read_stream, write_stream):
        try:
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"SSE handler error: {e}", exc_info=True)


async def handle_health(request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "mcp-security-server",
        "version": "1.0.0"
    })


async def handle_root(request):
    """Root endpoint."""
    return JSONResponse({
        "name": "MCP Security Training Server",
        "version": "1.0.0",
        "endpoints": {
            "sse": "/sse",
            "health": "/health"
        }
    })


# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/", handle_root),
        Route("/health", handle_health),
        Route("/sse", handle_sse),
    ]
)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
