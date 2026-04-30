# Weather MCP Server

An MCP (Model Context Protocol) server with weather tools and a web GUI.

## Features

- **MCP Tool**: Expose weather tool to Claude/AI agents
- **Web GUI**: Streamlit-based web interface
- **Demo Mode**: Works without API key
- **Real API**: Supports OpenWeatherMap API

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get OpenWeatherMap API Key (Optional)

Sign up at https://openweathermap.org/api to get a free API key.

### 3. Run the MCP Server

```bash
# Run directly
python -m mcp_server

# Or using uvicorn
uvicorn mcp_server:app --reload
```

### 4. Run the Web GUI

```bash
streamlit run app.py
```

## Usage

### MCP Server

Configure your MCP client (VS Code, Cursor, etc.):

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/mcp_server"
    }
  }
}
```

Now you can use the weather tool in Claude:

```python
get_current_weather(location="London")
```

### Web GUI

Access the web interface at `http://localhost:8501` after running the app.

## API Reference

### Tool: `get_current_weather`

Get current weather for a location.

**Parameters:**
- `location` (string): City name
- `unit` (string): "celsius" or "fahrenheit" (default: "celsius")

**Returns:**
```json
{
  "location": "London",
  "country": "GB",
  "temperature": 15.5,
  "feels_like": 14.2,
  "description": "light rain",
  "humidity": 76,
  "pressure": 1013,
  "wind_speed": 4.2,
  "wind_direction": 245,
  "timestamp": 1609459200
}
```

## Project Structure

```
mcp_server/
├── mcp_server.py    # MCP server implementation
├── tools/           # Tools directory
│   ├── __init__.py  # Exports weather tools
│   └── weather_tool.py  # Weather API client
├── app.py           # Web GUI (Streamlit)
├── requirements.txt # Dependencies
└── README.md       # This file
```

## License

MIT
