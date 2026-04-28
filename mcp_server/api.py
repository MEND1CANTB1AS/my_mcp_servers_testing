from fastapi import FastAPI
from mcp_server.tools.calculator import calculate
from mcp_server.tools.weather import get_current_weather

# Initialize the FastAPI app
app = FastAPI(
    title="My MCP Server",
    description="A server exposing utility tools like calculator and weather info.",
    version="1.0.0",
)

# Manually register tools for demonstration purposes in the plan's scope
# In a real scenario, FastAPI dependency injection or specialized tool frameworks would handle this.
@app.get("/api/calculator")
def calculator_endpoint():
    """Use this tool for basic mathematical calculations."""
    return calculate

@app.get("/api/weather")
def weather_endpoint():
    """Use this tool to get the current weather for a specified location."""
    return get_current_weather