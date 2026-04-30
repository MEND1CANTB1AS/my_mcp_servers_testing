"""Entry point for running the MCP server as a module."""
import uvicorn
from mcp_server import mcp

if __name__ == "__main__":
    # Start MCP server
    uvicorn.run(__name__ + ":app", host="127.0.0.1", port=8000)
