"""
Simplified MCP server using stdio transport for testing.
This can help debug the MCP protocol separately from SSE.
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from .logging_config import get_logger
from .tools import network, web, cloud, binary, exploit

logger = get_logger(__name__)

# Create MCP server
server = Server("mcp-security-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available security tools."""
    tools = []
    for module in [network, web, cloud, binary, exploit]:
        tools.extend(module.list_tools())
    logger.info(f"Listed {len(tools)} tools")
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a security tool."""
    logger.info(f"Calling tool: {name} with args: {arguments}")

    # Get all tool handlers
    handlers = {}
    for module in [network, web, cloud, binary, exploit]:
        for tool_info in module.get_tools():
            handlers[tool_info["name"]] = tool_info["handler"]

    if name not in handlers:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        result = await handlers[name](**arguments)
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
