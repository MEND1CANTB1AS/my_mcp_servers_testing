import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../..', '.env'))

def get_api_key() -> Optional[str]:
    """Retrieves the Weather API key from environment variables."""
    return os.getenv("OPENWEATHER_API_KEY")

def get_current_weather(location: str, unit: str = "celsius") -> dict:
    """
    Get the current weather in a given location.
    The 'unit' parameter must be 'celsius' or 'fahrenheit'.
    """
    api_key = get_api_key()
    if not api_key:
        return {"error": "Weather API key not configured. Please check the .env file."}

    # Placeholder for actual API call using the key
    # The actual implementation will use an HTTP client to query the OpenWeatherMap API
    print(f"Simulating API call for weather in {location}...")

    if "London" in location:
        return {"location": location, "temperature": "15", "unit": unit, "description": "Cloudy"}
    else:
        return {"location": location, "temperature": "22", "unit": unit, "description": "Sunny"}