"""Web GUI for Weather MCP Server using Streamlit"""
import streamlit as st
import requests
from tools import get_weather


def get_weather_data(location: str, unit: str = "celsius") -> dict:
    """Fetch weather data from OpenWeatherMap API."""
    # Get API key from streamlit secrets
    api_key = st.secrets.get("OPENWEATHER_API_KEY", "") if st.secrets.get("OPENWEATHER_API_KEY") else None

    if not api_key:
        # Demo mode - use demo API key
        api_key = "demo"

    # Use the tools module's get_weather function
    result = get_weather(location, unit)
    return result


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Weather MCP Server",
        page_icon="🌤️",
        layout="wide"
    )

    st.title("🌤️ Weather MCP Server")

    # Sidebar for API key configuration
    with st.sidebar:
        st.header("Configuration")

        api_key = st.text_input(
            "OpenWeatherMap API Key",
            type="password",
            help="Optional. Leave empty to use demo mode."
        )

        if api_key:
            st.success(f"API key configured ({len(api_key)} chars)")
            st.secrets["OPENWEATHER_API_KEY"] = api_key

        st.markdown("---")

        st.info("""
        ### About
        This is a web GUI for the Weather MCP Server.

        **MCP Server**: Provides weather tool to Claude Agent
        **API**: Uses OpenWeatherMap API
        **Demo mode**: Available without API key
        """)

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Query Weather")
        location = st.text_input("City name", placeholder="e.g., London")

        unit_options = {
            "°C (Celsius)": "celsius",
            "°F (Fahrenheit)": "fahrenheit"
        }
        unit = st.selectbox("Temperature Unit", options=list(unit_options.keys()), index=0)
        unit_value = unit_options[unit]

        # Weather icon mapping
        weather_icons = {
            "Clear": "☀️",
            "Clouds": "⛅",
            "Rain": "🌧️",
            "Drizzle": "🌦️",
            "Thunderstorm": "⚡",
            "Snow": "❄️",
            "Mist": "🌫️",
            "Smoke": "🌫️",
            "Haze": "🌫️",
            "Dust": "🌪️",
            "Ash": "🌋",
            "Squall": "🌬️",
            "Tornado": "🌪️"
        }

        if st.button("Get Weather", type="primary", use_container_width=True):
            if location:
                with st.spinner(f"Fetching weather for {location}..."):
                    data = get_weather_data(location, unit_value)

                    if "error" in data:
                        st.error(f"Error: {data['error']}")
                    else:
                        st.success(f"Found: {data['location']}, {data['country']}")

                        # Display weather info
                        icon_str = weather_icons.get(data["description"].split()[0], "☁️")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown(f"**{icon_str} {data['description'].title()}**")
                            st.metric(
                                "Temperature",
                                f"{data['temperature']}°{unit}",
                                delta=f"Feels like {data['feels_like']}°{unit}"
                            )

                        with col2:
                            st.dataframe(
                                {
                                    "Humidity": f"{data['humidity']}%",
                                    "Pressure": f"{data['pressure']} hPa",
                                    "Wind Speed": f"{data['wind_speed']} m/s"
                                },
                                use_container_width=True
                            )

                        with col3:
                            st.info(f"**Location**: {data['location']}, {data['country']}")
                            st.caption(f"Data at: {data['timestamp']}")

            else:
                st.warning("⚠️ Please enter a city name")

    with col2:
        st.subheader("MCP Server Info")

        st.code("from mcp.server.fastmcp import FastMCP\nfrom tools.weather_tool import get_weather\n\nmcp = FastMCP('weather-server')\n\n@mcp.tool()\nasync def get_current_weather(location: str, unit: str = 'celsius'):\n    \"\"\"Get weather for a location.\"\"\"\n    result = get_weather(location, unit)\n    return result", language="python")

        st.markdown("""
        ### How to use:

        1. **MCP Client**: Connect to this server using:
           ```python
           from mcp_server import mcp
           ```

        2. **Direct API**: Use the web interface above

        3. **Claude**: Use via MCP configuration:
           ```json
           {
             "mcpServers": {
               "weather": {
                 "command": "python",
                 "args": ["-m", "mcp_server"]
               }
             }
           }
           ```
        """)

        # Add some examples
        examples = [
            "get_current_weather(location='London')",
            "get_current_weather(location='Tokyo')",
            "get_current_weather(location='New York')"
        ]

        st.write("**Common MCP Tool calls:**")
        for example in examples:
            st.code(example, language="python")


if __name__ == "__main__":
    main()
