"""MCP Server with Weather Tools"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent to path to import from tools directory
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("weather-server", instructions="Weather API MCP Server")

# Import tools from the tools directory
from tools import get_weather

@mcp.tool()
async def get_current_weather(location: str, unit: str = "celsius") -> dict:
    """
    Get current weather for a location.

    Args:
        location: City name (e.g., "London", "New York")
        unit: Temperature unit ("celsius" or "fahrenheit")

    Returns:
        Weather data dictionary with temperature, description, humidity, etc.
    """
    result = get_weather(location, unit)
    return result


# Register a resource for documentation
@mcp.resource("weather://docs")
def weather_docs():
    return """
    Weather MCP Server

    Tools:
    - get_current_weather: Get current weather for any city

    Usage:
    - Provide a city name to get current weather
    - Default unit is celsius (change to fahrenheit)

    Example: get_current_weather(location="London")
    """
