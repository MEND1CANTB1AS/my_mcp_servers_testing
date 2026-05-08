"""MCP Server Package"""
from .mcp_server import mcp

# Create the FastMCP server instance
app = mcp.streamable_http_app()
