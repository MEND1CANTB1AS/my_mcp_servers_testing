#!/usr/bin/env python3
"""
View crawl results from the web_crawler tool.
Displays screenshots, metadata, and extracted content.
"""

import asyncio
import base64
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler


async def view_crawl_results(url: str, output_dir: str = "./crawl_results"):
    """Crawl and display results."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🕷️  Crawling: {url}\n")
    print("-" * 60)

    crawler = AsyncWebCrawler(headless=True)
    try:
        result = await crawler.arun(url=url, wait_for=None)
        r = result._results[0]

        # Save results
        results_file = output_dir / f"results_{Path(url).name[:50]}.json"
        screenshot_file = output_dir / f"screenshot_{Path(url).name[:50]}.png"

        # Save JSON results
        save_dict = {
            "url": r.url,
            "title": r.metadata.get("title", "N/A"),
            "status_code": r.status_code,
            "success": r.success,
            "final_url": r.redirected_url,
            "html_size": len(r.html),
            "markdown_size": len(r.markdown) if r.markdown else 0,
            "extracted_content_size": len(r.extracted_content) if r.extracted_content else 0,
            "metadata": r.metadata,
            "links_count": len(r.links) if r.links else 0,
            "tables_count": len(r.tables) if r.tables else 0,
            "screenshots": [],
            "error": r.error_message,
        }

        if r.screenshot:
            # Save screenshot
            screenshot_data = base64.b64decode(r.screenshot)
            with open(screenshot_file, "wb") as f:
                f.write(screenshot_data)

            save_dict["screenshots"] = [{
                "path": screenshot_file.name,
                "size": len(screenshot_data),
                "scales": r.screenshot_scales
            }]

        # Pretty print metadata
        if r.metadata:
            print(f"\n📄 Title: {r.metadata.get('title', 'N/A')}")
            print(f"🌐 URL: {r.url}")
            print(f"📊 Status: {r.status_code}")
            print(f"✅ Success: {r.success}")
            print(f"\n📏 Size:")
            print(f"   - HTML: {len(r.html):,} bytes ({len(r.html)/1024:.1f} KB)")
            print(f"   - Markdown: {len(r.markdown) if r.markdown else 0:,} bytes")
            print(f"   - Extracted Content: {len(r.extracted_content) if r.extracted_content else 0:,} bytes")

        # Show links
        if r.links and len(r.links) > 0:
            print(f"\n🔗 Links found: {len(r.links)}")
            for i, link in enumerate(r.links, 1):  # Show all
                # Handle both string and dict formats
                if isinstance(link, str):
                    text = link.strip()[:50]
                    link_url = link
                else:
                    text = link.get("text", "").strip()[:50] if link.get("text") else ""
                    link_url = link.get("url", "N/A")
                print(f"   {i}. [{text}]({link_url})")

        # Show tables
        if r.tables:
            print(f"\n📋 Tables found: {len(r.tables)}")

        # Show metadata keys
        if r.metadata:
            print(f"\n📝 Metadata keys:")
            for key in r.metadata.keys():
                print(f"   - {key}")

        # Show extracted markdown content
        if r.markdown:
            print(f"\n📄 Extracted markdown content ({len(r.markdown):,} bytes):")
            print("-" * 40)
            # Print first 2000 chars
            print(r.markdown[:2000])
            if len(r.markdown) > 2000:
                print("... (content truncated)")

        # Save to JSON
        with open(results_file, "w") as f:
            json.dump(save_dict, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {results_file}")
        if screenshot_file.exists():
            print(f"   Screenshot saved to: {screenshot_file}")

        return save_dict

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None
    finally:
        await crawler.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    else:
        url = "https://www.nfl.com/"

    results = asyncio.run(view_crawl_results(url))
    if results:
        print("\n✅ Crawl completed successfully!")
    else:
        print("\n❌ Crawl failed!")
