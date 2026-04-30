"""
Standalone Web GUI for Weather MCP Server
Run with: streamlit run web_app.py
"""
import streamlit as st
import requests
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Weather MCP Server",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def get_weather_data(location: str, unit: str = "celsius") -> dict:
    """Fetch weather data from OpenWeatherMap API."""
    # Try to get API key from environment or config
    api_key = st.secrets.get("OPENWEATHER_API_KEY", "") if hasattr(st, 'secrets') and st.secrets.get("OPENWEATHER_API_KEY") else None

    if not api_key:
        # Demo mode
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": "demo",
            "units": "metric" if unit == "celsius" else "imperial"
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"]["deg"],
                "timestamp": data["dt"],
                "timezone": data["timezone"]
            }
        except Exception as e:
            return {"error": str(e)}
    else:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric" if unit == "celsius" else "imperial"
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"]["deg"],
                "timestamp": data["dt"],
                "timezone": data["timezone"]
            }
        except Exception as e:
            return {"error": str(e)}


def weather_icon(weather_type: str) -> str:
    """Convert weather description to emoji icon."""
    type = weather_type.split()[0].lower()
    icon_map = {
        "clear": "☀️",
        "clouds": "⛅",
        "rain": "🌧️",
        "drizzle": "🌦️",
        "thunderstorm": "⚡",
        "snow": "❄️",
        "mist": "🌫️",
        "smoke": "🌫️",
        "haze": "🌫️",
        "dust": "🌪️",
        "fog": "🌫️",
        "sand": "🏜️",
        "ash": "🌋",
        "squall": "🌬️",
        "tornado": "🌪️"
    }
    return icon_map.get(type, "🌤️")


def main():
    """Main app function."""
    st.title("🌤️ Weather MCP Server")
    st.markdown("Get real-time weather data via MCP tool or web interface")

    col1, col2 = st.columns(2)

    # Sidebar
    with col1:
        st.header("Settings")

        # API Key
        api_key = st.text_input(
            "OpenWeatherMap API Key",
            type="password",
            help="Optional. Leave empty for demo mode."
        )

        if api_key:
            st.success("✅ API key configured")
            st.secrets["OPENWEATHER_API_KEY"] = api_key

        st.markdown("---")

        # About section
        st.markdown("""
        **About this tool**

        - **MCP Server**: Provides weather tool to AI agents
        - **Web GUI**: Streamlit-based interface
        - **API**: OpenWeatherMap or demo mode

        ### Example MCP Usage
        ```python
        get_current_weather(location="London")
        ```
        """)

    # Query Section
    with col2:
        st.header("Query Weather")

        location = st.text_input(
            "City",
            placeholder="e.g., London, Tokyo, New York"
        )

        unit_options = {
            "°C (Celsius)": "celsius",
            "°F (Fahrenheit)": "fahrenheit"
        }
        unit_label = st.selectbox("Temperature Unit", list(unit_options.keys()), index=0)
        unit_value = unit_options[unit_label]

        weather_btn = st.button("Get Weather", type="primary", use_container_width=True)

        if weather_btn and location:
            with st.spinner(f"Fetching weather for {location}..."):
                data = get_weather_data(location, unit_value)

                if "error" in data:
                    st.error(f"❌ Error: {data['error']}")
                else:
                    st.success(f"✅ Found: {data['location']}, {data['country']}")

                    # Main weather card
                    icon = weather_icon(data["description"])
                    st.markdown(f"""
                    <div class="weather-card">
                    <div style="font-size: 4em;">{icon}</div>
                    <div style="font-size: 1.5em; margin-top: 10px;">
                    {data['description'].title()}
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Metrics
                    temp_unit = "°C" if unit_value == "celsius" else "°F"
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                        <div style="font-size: 2em;">{temp_unit}</div>
                        <div style="font-size: 1.2em;">{data['temperature']:.1f}</div>
                        <div style="font-size: 0.9em;">Current</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                        <div style="font-size: 2em;">💨</div>
                        <div style="font-size: 1.2em;">{data['wind_speed']:.1f} m/s</div>
                        <div style="font-size: 0.9em;">Wind</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                        <div style="font-size: 2em;">💧</div>
                        <div style="font-size: 1.2em;">{data['humidity']}%</div>
                        <div style="font-size: 0.9em;">Humidity</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Additional info
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.info(f"**Feels like:** {data['feels_like']:.1f}°{temp_unit}")

                    with col2:
                        st.info(f"**Pressure:** {data['pressure']} hPa")

                    with col3:
                        st.info(f"**Direction:** {data['wind_direction']}°")

                    st.caption(f"Data timestamp: {datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M')} UTC")

        elif weather_btn and not location:
            st.warning("⚠️ Please enter a city name")

    # Info section at bottom
    st.markdown("---")
    st.markdown("""
    ### MCP Server Integration

    Add this to your `.claude.json` or MCP configuration:

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

    Then use in Claude:
    ```
    What's the weather in London?
    ```
    """)


if __name__ == "__main__":
    main()
