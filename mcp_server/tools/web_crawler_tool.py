"""
Web Crawler MCP Tool with Retrieval-Augmented Generation (RAG).

This tool uses crawl4ai for headless browser-based web crawling,
extracts relevant content, and uses keyword-based retrieval to answer
questions about web content.
"""
import json
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler


class SimpleVectorStore:
    """Simple keyword-based vector store for RAG retrieval."""

    def __init__(self):
        self.index = {}
        self.documents = {}

    def index_document(self, url: str, content: str, chunks: list):
        """Index a document and its chunks."""
        self.documents[url] = {
            "url": url,
            "content": content,
            "chunks": chunks
        }

        # Create keyword indices for retrieval
        for chunk in chunks:
            # Extract keywords (common words removed)
            keywords = self._extract_keywords(chunk)

            # Add to index
            for keyword in keywords:
                if keyword not in self.index:
                    self.index[keyword] = []
                # Add chunk info with URL and position
                self.index[keyword].append({
                    "url": url,
                    "chunk": chunk,
                    "score": 1.0
                })

    def _extract_keywords(self, text: str, num_keywords: int = 5) -> list:
        """Extract important keywords from text."""
        # Remove punctuation and convert to lowercase
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)

        # Tokenize
        words = text.split()

        # Filter out common stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what',
            'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
            'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'also', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once', 'if', 'as'
        }

        # Count word frequencies
        word_freq = {}
        for word in words:
            word = word.strip()
            if len(word) > 2 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top keywords by frequency
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:num_keywords]]

    def search(self, query: str, top_k: int = 5) -> list:
        """Search for relevant content using keyword matching."""
        # Extract keywords from query
        query_keywords = self._extract_keywords(query, num_keywords=8)

        if not query_keywords:
            return []

        # Score chunks based on keyword matching
        results = []

        for chunk_id, chunk in self.documents.items():  # noqa: F841
            chunk_text = chunk["content"].lower()
            chunk_keywords = self._extract_keywords(chunk_text, num_keywords=10)

            # Calculate overlap between query and chunk keywords
            overlap = set(query_keywords) & set(chunk_keywords)
            score = len(overlap)  # noqa: F841

            if score > 0:
                # Normalize score and add position info
                results.append({
                    "url": chunk["url"],
                    "chunk": chunk,
                    "score": score,
                    "query_keywords": query_keywords,
                    "matched_keywords": list(overlap)
                })

        # Sort by score and take top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class WebCrawlerTool:
    """MCP Tool for web crawling with RAG capabilities using crawl4ai."""

    def __init__(self):
        self.crawler = None
        self.vector_store = SimpleVectorStore()
        self.max_depth = 2  # Maximum number of pages to crawl from each link
        self.max_links = 100  # Maximum number of links to follow
        self.timeout = 10  # Request timeout in seconds

    async def init_crawler(self):
        """Initialize crawl4ai crawler if not already initialized."""
        if self.crawler is None:
            self.crawler = AsyncWebCrawler(verbose=False, headless=True)
            await self.crawler.start()

    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch and parse a URL using crawl4ai."""
        try:
            await self.init_crawler()

            # Fetch the page using crawl4ai
            result = await self.crawler.arun(url)

            if not result.success:
                return None

            # Generate markdown from the crawled content
            md_generator = MarkdownGenerator()
            markdown = md_generator.generate_markdown(result)

            # Remove script, style, and hidden elements from markdown
            import re
            markdown = re.sub(r'<script[^>]*>.*?</script>', '', markdown, flags=re.DOTALL)
            markdown = re.sub(r'<style[^>]*>.*?</style>', '', markdown, flags=re.DOTALL)
            markdown = re.sub(r'<noscript[^>]*>.*?</noscript>', '', markdown, flags=re.DOTALL)
            markdown = re.sub(r'<iframe[^>]*>.*?</iframe>', '', markdown, flags=re.DOTALL)

            # Extract text with reasonable length
            text = markdown.strip()
            text = re.sub(r'\s+', ' ', text)

            # Limit text length
            if len(text) > 50000:
                text = text[:50000] + "..."

            return text

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def extract_links(self, result) -> list:
        """Extract links from a crawled page using crawl4ai result."""
        links = []

        if not result or not result.html:
            return links

        # Extract links from the HTML content
        link_pattern = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, result.html, re.IGNORECASE)

        for href, link_text in matches:
            # Skip anchors and javascript links
            if '#' in href or href.lower().startswith(('javascript:', 'mailto:', 'tel:')):
                continue

            # Build full URL
            if href.startswith('//'):
                full_url = 'https:' + href
            elif href.startswith('/'):
                domain = urlparse(result.url).netloc
                path = result.url.split('/', 3)[3] if len(result.url.split('/')) > 3 else ''
                full_url = f"https://{domain}/{path}/{href}" if path else f"https://{domain}{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                base_path = result.url.rsplit('/', 1)[0]
                full_url = f"{base_path}/{href}"

            if full_url not in links:
                links.append(full_url)

        return links

    async def chunk_content(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks."""
        chunks = []
        text = text.strip()

        # Split by paragraphs or sentences
        paragraphs = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 <= chunk_size:
                current_chunk += para + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = para + " "

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    async def crawl(self, url: str, max_links: Optional[int] = None, max_depth: Optional[int] = None) -> dict:
        """Crawl a URL and its linked pages using crawl4ai."""
        max_links = max_links or self.max_links
        max_depth = max_depth or self.max_depth

        # Extract domain for filtering (must be before nested function uses it)
        base_domain = urlparse(url).netloc

        await self.init_crawler()

        visited = set()
        all_chunks = []
        crawled_urls = []

        async def crawl_page(page_url: str, depth: int = 0):
            if depth > max_depth or len(visited) >= max_links:
                return

            # Check if visited
            if page_url in visited:
                return
            visited.add(page_url)

            # Fetch and parse page using crawl4ai
            text = await self.fetch_url(page_url)
            if not text:
                return

            # Extract title from the result
            result = await self.crawler.arun(page_url)
            title = result.title if result.success else None

            # Parse HTML for link following
            html = result.html if result.success else ""
            soup_links = self._extract_links_from_html(html)

            # Add to crawled URLs list
            crawled_urls.append({
                "url": page_url,
                "title": title,
                "domain": self._extract_domain(page_url)
            })

            # Chunk content
            chunks = self.chunk_content(text)

            # Index chunks
            self.vector_store.index_document(page_url, text, chunks)
            all_chunks.extend(chunks)

            # Follow links
            for link in soup_links:
                if link in visited:
                    continue

                # Domain filter - allow same domain and subdomains
                link_domain = urlparse(link).netloc
                # Allow same domain or subdomain (e.g., docs.python.org from python.org)
                is_same_domain = (
                    link_domain == base_domain or
                    link_domain.endswith('.' + base_domain)
                )
                if link_domain and is_same_domain:
                    await crawl_page(link, depth + 1)

        await crawl_page(url)

        return {
            "initial_url": url,
            "crawled_pages": crawled_urls,
            "total_pages": len(crawled_urls),
            "indexed_chunks": len(all_chunks)
        }

    def _extract_links_from_html(self, html: str) -> list:
        """Extract links from HTML content."""
        links = []

        if not html:
            return links

        # Extract links from the HTML content
        import re
        link_pattern = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, html, re.IGNORECASE)

        for href, _ in matches:
            # Skip anchors and javascript links
            if '#' in href or href.lower().startswith(('javascript:', 'mailto:', 'tel:')):
                continue

            # Build full URL
            if href.startswith('//'):
                full_url = 'https:' + href
            elif href.startswith('/'):
                domain = urlparse(html.split('src')[0] if 'src' in html else 'about:blank').netloc
                if not domain:
                    domain = html.split('/')[0].split(':')[0]
                    full_url = f"https://{domain}{href}"
                else:
                    path = html.split('/', 3)[3] if len(html.split('/')) > 3 else ''
                    full_url = f"https://{domain}/{path}/{href}" if path else f"https://{domain}{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                base_path = html.rsplit('/', 1)[0]
                full_url = f"{base_path}/{href}"

            if full_url not in links:
                links.append(full_url)

        return links

    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title from HTML."""
        if not html:
            return None

        # Try to find title tag
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()

        # Try h1
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()

        return None

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split('/')[0]

    async def get_relevant_content(self, query: str, top_k: int = 5) -> list:
        """Get relevant content chunks for a query using RAG."""
        results = self.vector_store.search(query, top_k)

        content = []
        for result in results:
            chunk_data = result["chunk"]
            content.append({
                "url": result["url"],
                "content": chunk_data.get("content", ""),
                "keywords": result.get("matched_keywords", []),
                "score": result.get("score", 0)
            })

        return content


# Create singleton instance
web_crawler = WebCrawlerTool()


async def get_current_web_content(location: str, max_links: Optional[int] = None, max_depth: Optional[int] = None) -> dict:
    """
    Fetch and crawl a URL, returning indexed content for RAG queries.

    Args:
        location: URL to crawl
        max_links: Maximum number of links to follow (default from config)
        max_depth: Maximum crawl depth (default from config)

    Returns:
        Dictionary with crawled pages and indexed content
    """
    # Clear previous index for fresh crawl
    web_crawler.vector_store = SimpleVectorStore()

    result = await web_crawler.crawl(location, max_links, max_depth)

    return result


async def search_web_content(query: str, top_k: int = 5) -> list:
    """
    Search indexed web content using RAG retrieval.

    Args:
        query: Search query string
        top_k: Number of results to return

    Returns:
        List of relevant content chunks with metadata
    """
    return await web_crawler.get_relevant_content(query, top_k)


async def get_web_summary(url: str, query: str) -> str:
    """
    Get a summary answering a query about a specific web page.

    Args:
        url: URL to analyze
        query: Question to answer about the page

    Returns:
        Summary answer based on the page content
    """
    # Clear and re-index
    web_crawler.vector_store = SimpleVectorStore()

    # Fetch content
    text = await web_crawler.fetch_url(url)
    if not text:
        return f"Could not fetch content from {url}"

    # Index
    chunks = web_crawler.chunk_content(text)
    web_crawler.vector_store.index_document(url, text, chunks)

    # Search and summarize
    results = await web_crawler.get_relevant_content(query, top_k=3)

    if not results:
        return f"No relevant content found for '{query}' in {url}"

    # Build summary
    summary_parts = []
    for i, result in enumerate(results, 1):
        summary_parts.append(f"{i}. {result['content']}")

    return " ".join(summary_parts)
