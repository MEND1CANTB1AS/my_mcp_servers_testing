# My MCP Server Deployment and Testing Guide

## 🚀 Getting Started

This project establishes a Multi-Tool Cloud Prompting (MCP) Server, allowing a language model to access utility functions like calculation and weather retrieval through a single API interface.

### Prerequisites
1. Python 3.9+
2. FastAPI
3. python-dotenv
4. The OpenWeatherMap API library (or similar HTTP client)

### 🛠 Setup Steps
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: A `requirements.txt` file should be created listing all dependencies.)*

2. **Configure API Key:**
   Create a `.env` file in the `mcp_server/config` directory and populate your actual API key:
   ```
   # .env
   OPENWEATHER_API_KEY="your_actual_openweather_api_key"
   ```

3. **Run Locally:**
   Start the server using the following command:
   ```bash
   uvicorn mcp_server.api:app --reload
   ```
   The server should be accessible at `http://localhost:8000/docs`.

## ✅ Testing the Tools

### 1. Unit Tests (Code Logic)
Run the unit tests in the `mcp_server/tests` directory to validate the internal logic of the tools.
```bash
python -m unittest mcp_server.tests.test_tools
```

### 2. API Integration Tests (End-to-End)
Use the Swagger UI (`/docs`) provided by FastAPI to test the exposed endpoints (`/api/calculator` and `/api/weather`) against the running server instance.

## 🔄 Deployment Guide

### Testing the Prompting Layer
After the server is running and the tools are functional, the final layer to test is the model's ability to use the tools.
1. **Model Testing:** Provide prompts to the MCP Server API that require both tools (e.g., "What is the calculation result of 5 times the current temperature in London?").
2. **Evaluation:** Verify that the model correctly:
    a. Identifies the need for both tools.
    b. Calls the tools in the correct order.
    c. Synthesizes a final, natural language answer using both tool outputs.

### Production Deployment
For production, consider using a dedicated deployment platform (e.g., AWS Lambda, Docker container on Kubernetes) and ensure API keys are managed via a secure secret manager, not directly in `.env` files.
