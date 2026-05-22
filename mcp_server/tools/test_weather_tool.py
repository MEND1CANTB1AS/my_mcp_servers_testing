"""Unit tests for weather_tool.py"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import tomllib

import requests

from weather_tool import get_weather


@pytest.fixture
def mock_api_response_celsius():
    """Mock API response for a celsius weather query."""
    return {
        "name": "London",
        "sys": {"country": "GB"},
        "main": {
            "temp": 12.5,
            "feels_like": 11.0,
            "humidity": 75,
            "pressure": 1013
        },
        "weather": [{"description": "broken clouds", "main": "Clouds"}],
        "wind": {"speed": 5.2, "deg": 240},
        "dt": 1704067200,
        "timezone": 3600
    }


@pytest.fixture
def mock_api_response_fahrenheit():
    """Mock API response for a fahrenheit weather query."""
    return {
        "name": "New York",
        "sys": {"country": "US"},
        "main": {
            "temp": 55,
            "feels_like": 52,
            "humidity": 60,
            "pressure": 1015
        },
        "weather": [{"description": "clear sky", "main": "Clear"}],
        "wind": {"speed": 8.5, "deg": 320},
        "dt": 1704067200,
        "timezone": -18000
    }


@pytest.fixture
def mock_api_response_uk():
    """Mock API response for a UK location."""
    return {
        "name": "Manchester",
        "sys": {"country": "GB"},
        "main": {
            "temp": 8.0,
            "feels_like": 6.5,
            "humidity": 82,
            "pressure": 1008
        },
        "weather": [{"description": "light rain", "main": "Rain"}],
        "wind": {"speed": 6.1, "deg": 220},
        "dt": 1704067200,
        "timezone": 0
    }


@pytest.fixture
def secrets_file_celsius():
    """Create a secrets file with celsius unit preference."""
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    secrets_content = {
        "OPENWEATHER_API_KEY": "test_api_key_12345"
    }
    with open(secrets_path, "wb") as f:
        f.write(tomllib.dumps(secrets_content).encode())
    return secrets_path


@pytest.fixture
def secrets_file_fahrenheit():
    """Create a secrets file with fahrenheit unit preference."""
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    secrets_content = {
        "OPENWEATHER_API_KEY": "test_api_key_67890",
        "OPENWEATHER_UNIT": "fahrenheit"
    }
    with open(secrets_path, "wb") as f:
        f.write(tomllib.dumps(secrets_content).encode())
    return secrets_path


@pytest.fixture
def mock_requests_response_celsius(mock_api_response_celsius):
    """Mock requests.get response for celsius query."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_celsius
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_requests_response_fahrenheit(mock_api_response_fahrenheit):
    """Mock requests.get response for fahrenheit query."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_fahrenheit
    mock_response.raise_for_status.return_value = None
    return mock_response


class TestGetWeather:
    """Test cases for get_weather function."""

    @patch("requests.get")
    def test_get_weather_celsius(self, mock_get, mock_requests_response_celsius):
        """Test getting weather in celsius with API key."""
        mock_get.return_value = mock_requests_response_celsius

        result = get_weather("London", "celsius")

        # Verify API call parameters
        mock_get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": "London",
                "appid": "test_api_key_12345",
                "units": "metric"
            },
            timeout=10
        )

        # Verify result structure
        assert result["location"] == "London"
        assert result["country"] == "GB"
        assert result["temperature"] == 12.5
        assert result["feels_like"] == 11.0
        assert result["description"] == "broken clouds"
        assert result["humidity"] == 75
        assert result["pressure"] == 1013
        assert result["wind_speed"] == 5.2
        assert result["wind_direction"] == 240
        assert result["timestamp"] == 1704067200
        assert result["timezone"] == 3600

    @patch("requests.get")
    def test_get_weather_fahrenheit(self, mock_get, mock_requests_response_fahrenheit):
        """Test getting weather in fahrenheit with API key."""
        mock_get.return_value = mock_requests_response_fahrenheit

        result = get_weather("New York", "fahrenheit")

        # Verify API call parameters
        mock_get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": "New York",
                "appid": "test_api_key_67890",
                "units": "imperial"
            },
            timeout=10
        )

        # Verify result structure
        assert result["location"] == "New York"
        assert result["country"] == "US"
        assert result["temperature"] == 55
        assert result["feels_like"] == 52
        assert result["description"] == "clear sky"
        assert result["humidity"] == 60
        assert result["pressure"] == 1015
        assert result["wind_speed"] == 8.5
        assert result["wind_direction"] == 320
        assert result["timestamp"] == 1704067200
        assert result["timezone"] == -18000

    @patch("requests.get")
    def test_get_weather_invalid_unit(self, mock_get):
        """Test that invalid unit defaults to celsius."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Test City",
            "sys": {"country": "XX"},
            "main": {"temp": 20, "feels_like": 18, "humidity": 50, "pressure": 1012},
            "weather": [{"description": "clear", "main": "Clear"}],
            "wind": {"speed": 3, "deg": 180},
            "dt": 1704067200,
            "timezone": 0
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_weather("Test City", "invalid_unit")

        # Should use celsius/units:metric for invalid unit
        mock_get.assert_called_once()
        assert mock_get.call_args[1]["params"]["units"] == "metric"

    @patch("requests.get")
    def test_get_weather_different_locations(self, mock_get, mock_api_response_generic):
        """Test that different locations work correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response_generic
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test various locations
        locations = ["Tokyo", "Sydney", "Paris", "Berlin", "Mumbai"]

        for location in locations:
            result = get_weather(location)
            assert result["location"] == location
            assert "country" in result
            assert "temperature" in result
            assert "description" in result

    @patch("requests.get")
    def test_get_weather_handles_missing_fields(self, mock_get):
        """Test graceful handling of incomplete API responses."""
        mock_response = MagicMock()
        # Incomplete response (missing some fields)
        mock_response.json.return_value = {
            "name": "Partial City",
            "sys": {"country": "XX"},
            "main": {"temp": 20},  # Missing other fields
            "weather": [{"description": "partial", "main": "Partial"}],
            "wind": {"speed": 5},  # Missing direction
            "dt": 1704067200,
            # Missing: feels_like, humidity, pressure, deg, timezone
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_weather("Partial City")

        # Should still return valid data with available fields
        assert result["location"] == "Partial City"
        assert result["temperature"] == 20
        assert result["description"] == "partial"
        assert result["wind_speed"] == 5

    @patch("requests.get")
    def test_get_weather_error_handling(self, mock_get):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=404)
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            get_weather("NonExistentCity123456789")

    @patch("requests.get")
    def test_get_weather_timeout(self, mock_get):
        """Test handling of timeout errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.ReadTimeout
        mock_get.return_value = mock_response

        with pytest.raises(requests.ReadTimeout):
            get_weather("London", timeout=0.001)

    @patch("requests.get")
    def test_get_weather_demo_mode(self, mock_get, mock_api_response_generic):
        """Test that demo mode works when no API key is available."""
        # Remove any existing secrets file
        secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            secrets_path.unlink()

        # Also remove environment variable
        with patch.dict("os.environ", {"OPENWEATHER_API_KEY": ""}):
            mock_response = MagicMock()
            mock_response.json.return_value = mock_api_response_generic
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = get_weather("London")

            # Should work in demo mode
            assert result["location"] == "London"
            mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_weather_with_environment_variable(self, mock_get, mock_api_response_generic):
        """Test that environment variable API key is used."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response_generic
        mock_response.raise_for_status.return_value = None

        # Set environment variable
        with patch.dict("os.environ", {"OPENWEATHER_API_KEY": "env_api_key"}):
            mock_get.return_value = mock_response

            result = get_weather("London")

            # Should use env var API key
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["params"]["appid"] == "env_api_key"

    @patch("requests.get")
    def test_get_weather_response_structure(self, mock_get, mock_api_response_generic):
        """Test that response has correct structure with all expected fields."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response_generic
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_weather("Test Location")

        # Check all expected fields are present
        expected_fields = {
            "location": str,
            "country": str,
            "temperature": (int, float),
            "feels_like": (int, float),
            "description": str,
            "humidity": int,
            "pressure": int,
            "wind_speed": (int, float),
            "wind_direction": int,
            "timestamp": int,
            "timezone": int
        }

        for field, field_type in expected_fields.items():
            assert field in result, f"Missing field: {field}"
            assert isinstance(result[field], field_type), f"Wrong type for {field}: {type(result[field])}"

    @patch("requests.get")
    def test_get_weather_edge_cases(self, mock_get):
        """Test edge cases like very high or low temperatures."""
        # High temperature
        high_temp_response = {
            "name": "Cairo",
            "sys": {"country": "EG"},
            "main": {"temp": 45.0, "feels_like": 48.0, "humidity": 20, "pressure": 1009},
            "weather": [{"description": "mostly clear", "main": "Clear"}],
            "wind": {"speed": 12.0, "deg": 350},
            "dt": 1704067200,
            "timezone": 7200
        }

        # Low temperature
        low_temp_response = {
            "name": "Iqaluit",
            "sys": {"country": "CA"},
            "main": {"temp": -30.0, "feels_like": -35.0, "humidity": 70, "pressure": 1020},
            "weather": [{"description": "snow showers", "main": "Snow"}],
            "wind": {"speed": 30.0, "deg": 30},
            "dt": 1704067200,
            "timezone": -18000
        }

        # Test high temperature
        mock_response = MagicMock()
        mock_response.json.return_value = high_temp_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_weather("Cairo")
        assert result["temperature"] == 45.0
        assert result["feels_like"] == 48.0

        # Test low temperature
        mock_response.json.return_value = low_temp_response
        mock_get.return_value = mock_response

        result = get_weather("Iqaluit")
        assert result["temperature"] == -30.0
        assert result["feels_like"] == -35.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
