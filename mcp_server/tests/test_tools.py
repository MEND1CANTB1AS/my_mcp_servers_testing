import unittest
from mcp_server.tools.calculator import calculate
from mcp_server.tools.weather import get_current_weather
import os

# Mocking the environment for testing to prevent actual API calls
class MockAPI:
    def get_current_weather_mock(self, location: str, unit: str) -> dict:
        if "London" in location:
            return {"location": location, "temperature": "15", "unit": unit, "description": "Cloudy (Mocked)"}
        return {"location": location, "temperature": "22", "unit": unit, "description": "Sunny (Mocked)"}

# Mocking the .env file contents for testing
@classmethod
def setUpClass(cls):
    """Setup environment variables for testing."""
    os.environ["OPENWEATHER_API_KEY"] = "1bc0bb06321aabf22e2150924a5f2bb0"

class TestCalculator(unittest.TestCase):
    def test_simple_addition(self):
        # Test case for simple addition
        input_data = {"expression": "5 + 3"}
        # Note: This test assumes the 'calculate' function can be called directly for testing
        # In a real setup, we'd mock the entire 'calculate' call.
        # For simplicity here, we test the expected outcome structure.
        result = calculate(input_data)
        self.assertIn("result", result)
        self.assertEqual(result["result"], 8)

    def test_complex_expression(self):
        # Test case for complex arithmetic
        input_data = {"expression": "(10 * 2) / 5"}
        result = calculate(input_data)
        self.assertIn("result", result)
        self.assertEqual(result["result"], 4.0)

    def test_invalid_expression(self):
        # Test case for invalid syntax
        input_data = {"expression": "10 / (abc - 2")
        result = calculate(input_data)
        self.assertIn("error", result)

class TestWeather(unittest.TestCase):
    def test_get_weather_london(self):
        # Test case for a known location
        result = get_current_weather("London", "celsius")
        self.assertIn("Mocked", result["description"])
        self.assertEqual(result["location"], "London")

    def test_get_weather_other_location(self):
        # Test case for a different location
        result = get_current_weather("Tokyo", "fahrenheit")
        self.assertIn("Mocked", result["description"])
        self.assertEqual(result["location"], "Tokyo")

if __name__ == '__main__':
    unittest.main()