"""MCP Server with Weather and Web Crawler Tools"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent to path to import from tools directory
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("weather-server", instructions="""
Weather and Web Crawler MCP Server

Weather: Get current weather for any city using OpenWeatherMap API.

Web Crawler: Fetch and crawl web pages with Retrieval-Augmented Generation (RAG) capabilities.
- Crawl a URL and its linked pages
- Search indexed web content
- Get summaries answering queries about web pages

Supported tools:
- get_current_weather: Get current weather for a location
- crawl_url: Crawl a URL and index its content
- search_web_content: Search indexed web content with RAG retrieval
- get_web_summary: Get a summary answering a query about a specific web page
""")

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


@mcp.tool()
async def crawl_url(location: str, max_links: int = 5, max_depth: int = 1) -> dict:
    """
    Crawl a URL and index its content for RAG retrieval.

    Args:
        location: URL to crawl (e.g., "https://example.com")
        max_links: Maximum number of external links to follow
        max_depth: Maximum crawl depth

    Returns:
        Dictionary with crawled pages and indexed content count
    """
    # Clear previous index for fresh crawl
    from tools.web_crawler_tool import SimpleVectorStore, WebCrawlerTool
    web_crawler = WebCrawlerTool()
    web_crawler.vector_store = SimpleVectorStore()

    result = web_crawler.crawl(location, max_links, max_depth)
    return result


@mcp.tool()
async def search_web_content(query: str, top_k: int = 5) -> list:
    """
    Search indexed web content using RAG retrieval.

    Args:
        query: Search query string
        top_k: Number of results to return

    Returns:
        List of relevant content chunks with metadata
    """
    from tools.web_crawler_tool import SimpleVectorStore, WebCrawlerTool
    web_crawler = WebCrawlerTool()
    web_crawler.vector_store = SimpleVectorStore()
    return web_crawler.get_relevant_content(query, top_k)


@mcp.tool()
async def get_web_summary(url: str, query: str) -> str:
    """
    Get a summary answering a query about a specific web page.

    Args:
        url: URL to analyze
        query: Question to answer about the page

    Returns:
        Summary answer based on the page content
    """
    from tools.web_crawler_tool import SimpleVectorStore, WebCrawlerTool
    web_crawler = WebCrawlerTool()
    web_crawler.vector_store = SimpleVectorStore()

    text = web_crawler.fetch_url(url)
    if not text:
        return f"Could not fetch content from {url}"

    chunks = web_crawler.chunk_content(text)
    web_crawler.vector_store.index_document(url, text, chunks)

    results = web_crawler.get_relevant_content(query, top_k=3)

    if not results:
        return f"No relevant content found for '{query}' in {url}"

    # Build summary
    summary_parts = []
    for i, result in enumerate(results, 1):
        summary_parts.append(f"{i}. {result['content']}")

    return " ".join(summary_parts)


# Register a resource for documentation
@mcp.resource("web://docs")
def web_docs():
    return """
    Web Crawler MCP Server

    Tools:
    - crawl_url: Crawl a URL and index its content
    - search_web_content: Search indexed web content with RAG retrieval
    - get_web_summary: Get a summary answering a query about a specific web page

    Usage:
    - Crawl a URL first to index its content
    - Search the indexed content with relevant queries
    - Get summaries for specific questions about web pages

    Example workflow:
    - crawl_url("https://news.ycombinator.com")
    - search_web_content("artificial intelligence")
    - get_web_summary("https://news.ycombinator.com", "What are the top stories today?")
    """
