"""Weather API client for OpenWeatherMap."""
import os
import tomllib
from pathlib import Path
import requests


def get_weather(location: str, unit: str = "celsius") -> dict:
    """
    Fetch weather data from OpenWeatherMap API.

    Args:
        location: City name (e.g., "London", "New York")
        unit: Temperature unit ("celsius" or "fahrenheit")

    Returns:
        Weather data dictionary with temperature, description, humidity, etc.

    Note: The actual API call and authentication should be handled by the caller.
    This function returns a placeholder response when called directly.
    """
    # Get API key from secrets file or environment
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
                api_key = secrets.get("OPENWEATHER_API_KEY")
        except:
            api_key = None
    else:
        api_key = os.environ.get("OPENWEATHER_API_KEY")

    # Demo mode if no API key
    if not api_key:
        api_key = "demo"

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric" if unit == "celsius" else "imperial"
    }

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
