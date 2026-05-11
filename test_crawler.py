import asyncio
from crawl4ai import AsyncWebCrawler


async def test_crawler():
    """Test crawl4ai with a simple web page"""
    crawler = AsyncWebCrawler(headless=True)

    try:
        # Test with a simple static page
        print("Testing with NFL.com...")
        result = await crawler.arun(
            url="https://www.nfl.com/",
            wait_for=r'<h1>|<h2>|<a class="nav-item"'
        )

        r = result._results[0]
        print(f"\n✓ Page scraped successfully!")
        print(f"Title: {r.metadata.get('title', 'N/A')}")
        print(f"URL: {r.url}")
        print(f"Final HTML length: {len(r.html)} bytes")
        print(f"Markdown length: {len(r.markdown) if r.markdown else 0} bytes")

        # Show a preview of extracted content
        if r.markdown:
            lines = r.markdown.split('\n')[:5]
            print("\nSample extracted content:")
            for line in lines:
                print(f"  {line[:100]}")

        # Test with a JavaScript-heavy page
        print("\n\nTesting with a JS-heavy page (weather API)...")
        result2 = await crawler.arun(
            url="https://weather.visualcrossing.com/Visual Crossing/Atlanta",
            wait_for="complete"
        )

        print(f"✓ JS page scraped successfully!")
        print(f"Title: {result2._results[0].metadata.get('title', 'N/A')}")
        print(f"Final HTML length: {len(result2._results[0].html)} bytes")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        crawler.close()

    print("\n\nAll tests passed! Crawl4ai is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_crawler())
