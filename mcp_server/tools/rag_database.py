"""
Crawl4AI RAG Database Builder
Builds a Retrieval-Augmented Generation (RAG) database by crawling web pages
and storing their content in ChromaDB for semantic search.
"""
import chromadb
from chromadb.config import Settings
from crawl4ai import AsyncWebCrawler
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from urllib.parse import urlparse
import tomli as tomllib
from pathlib import Path
from typing import Optional
import asyncio
import json
import numpy as np


def create_rag_database(
    collection_name: str = "web_content",
    db_path: Optional[str] = None,
    persist_directory: Optional[str] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    verbose: bool = False,
):
    """
    Create a ChromaDB collection for RAG.

    Args:
        collection_name: Name of the collection
        db_path: Database path (for CLI usage)
        persist_directory: ChromaDB persistence directory
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        verbose: Print progress info

    Returns:
        dict: Database metadata
    """
    # Determine persistence directory
    if persist_directory:
        persist_dir = Path(persist_directory)
    else:
        persist_dir = Path(__file__).parent.parent.parent / ".chroma"

    if db_path:
        persist_dir = Path(db_path)

    persist_dir.mkdir(parents=True, exist_ok=True)

    # Create ChromaDB client with persistent storage
    chroma_path = str(persist_dir)
    if verbose:
        print(f"🗄️  Initializing ChromaDB at '{persist_dir}'...")
    chromadb_client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))

    # Get or create collection
    collection = chromadb_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Get embedder info
    if verbose:
        embedder_metadata = chromadb_client.get_collection(name=collection_name).metadata()
        print(f"📚 Collection '{collection_name}' initialized")
        print(f"   Embedder: {embedder_metadata['embedding_function_name']}")

    return {
        "path": str(persist_dir),
        "collection": collection_name,
    }


def crawl_and_index_pages(
    urls: list[str],
    chromadb_client: Optional[chromadb.Client] = None,
    collection_name: str = "web_content",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    verbose: bool = False,
) -> dict:
    """
    Crawl web pages and index them in ChromaDB.

    Args:
        urls: List of URLs to crawl
        chromadb_client: ChromaDB client (created if None)
        collection_name: ChromaDB collection name
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        verbose: Print progress info

    Returns:
        dict: Count of indexed chunks per URL
    """
    # Load from secrets
    secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
    secrets = {}
    if secrets_path.exists():
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)

    # Initialize embeddings and text splitter
    embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    # Get collection (create client if needed)
    if chromadb_client is None:
        db_path = Path(persist_directory) if 'persist_directory' in locals() else Path(__file__).parent.parent.parent / ".chroma"
        chroma_path = Path(db_path)
        chroma_path.mkdir(parents=True, exist_ok=True)
        chromadb_client = chromadb.PersistentClient(path=str(chroma_path))
        collection = chromadb_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    else:
        collection = chromadb_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    # Crawl and index
    results = {}
    crawler = AsyncWebCrawler()
    try:
        for url in urls:
            if verbose:
                print(f"\n🕷️  Crawling: {url}")

            try:
                result = asyncio.run(crawler.arun(url))

                if not result.success or not result.markdown:
                    if verbose:
                        print(f"❌ Failed to crawl {url}: {result.error or 'Unknown error'}")
                    results[url] = 0
                    continue

                # Get title from metadata
                title = result.metadata.get("title", "Untitled")

                # Split into chunks
                chunks = text_splitter.split_text(result.markdown)

                domain = url.split("//")[1].split("/")[0] if "//" in url else "unknown"

                # Create documents with metadata
                docs = [
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": url,
                            "title": title,
                            "domain": domain,
                            "timestamp": result.created_at.isoformat() if hasattr(result, "created_at") else None,
                        }
                    )
                    for chunk in chunks
                ]

                # Convert to dicts for Chroma add
                docs_dict = [
                    {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                    for doc in docs
                ]

                # Add to collection
                ids = collection.add(
                    documents=[d["page_content"] for d in docs_dict],
                    embeddings=embeddings.embed_documents([d["page_content"] for d in docs_dict]),
                    metadatas=[d["metadata"] for d in docs_dict],
                    ids=[f"{url}_{i}" for i in range(len(docs_dict))],
                )

                results[url] = len(ids)

            except Exception as e:
                if verbose:
                    print(f"❌ Error crawling {url}: {e}")
                results[url] = 0

    except Exception as e:
        print(f"\n❌ Error crawling pages: {e}")
    finally:
        crawler.close()

    return results


def query_rag(
    question: str,
    chromadb_client: Optional[chromadb.Client] = None,
    collection_name: str = "web_content",
    top_k: int = 3,
    filter_domain: Optional[str] = None,
    filter_min_score: float = 0.3,
    filter_title: Optional[str] = None,
    persist_directory: Optional[str] = None,
) -> list[dict]:
    """
    Query the RAG database for answers.

    Args:
        question: Query question
        chromadb_client: ChromaDB client (optional, will be created if None)
        collection_name: ChromaDB collection name
        top_k: Number of results to return
        filter_domain: Optional domain filter
        filter_min_score: Minimum similarity score threshold
        filter_title: Optional title filter (case-insensitive substring match)
        persist_directory: ChromaDB persistence directory

    Returns:
        List of (answer, source, score) tuples
    """
    # Load from secrets
    secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
    else:
        secrets = {}

    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})

    # Get collection (create client if needed)
    if chromadb_client is None:
        if persist_directory:
            db_path = Path(persist_directory)
        else:
            db_path = Path(__file__).parent.parent.parent / ".chroma"
        chroma_path = Path(db_path)
        chroma_path.mkdir(parents=True, exist_ok=True)
        chromadb_client = chromadb.PersistentClient(path=str(chroma_path))
        collection = chromadb_client.get_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    else:
        collection = chromadb_client.get_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    # Check if collection exists
    if collection.count() == 0:
        return []

    # Query collection
    query_results = collection.query(
        query_texts=[question],
        n_results=top_k,
        include=["documents", "embeddings", "metadatas"]
    )

    results = []
    if query_results and query_results.get("documents"):
        docs = query_results["documents"][0]

        for i, doc_data in enumerate(docs):
            # Get metadata
            metadata_list = query_results.get("metadatas", [[]])[0]
            if metadata_list:
                metadata = metadata_list[i] if i < len(metadata_list) else {}
            else:
                metadata = {}

            # Calculate similarity score using cosine similarity
            query_emb = embeddings.embed_query(question)
            doc_emb = embeddings.embed_documents([doc_data])[0]

            # Simple cosine similarity calculation
            similarity = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))

            score = similarity

            # Apply domain filter if provided
            domain = metadata.get("domain", "unknown")
            if filter_domain and domain != filter_domain:
                continue

            # Apply title filter if provided
            title = metadata.get("title", "")
            if filter_title and filter_title.lower() not in title.lower():
                continue

            if score >= filter_min_score:
                results.append({
                    "answer": doc_data,
                    "source": metadata.get("source", "unknown"),
                    "domain": domain,
                    "title": title,
                    "score": score,
                })

    return results


def get_statistics(chromadb_client: Optional[chromadb.Client] = None, collection_name: str = "web_content", persist_directory: Optional[str] = None) -> dict:
    """Get database statistics."""
    # Get collection info (create client if needed)
    try:
        if chromadb_client is None and persist_directory is not None:
            db_path = Path(persist_directory)
            chroma_path = Path(db_path)
            chroma_path.mkdir(parents=True, exist_ok=True)
            chromadb_client = chromadb.PersistentClient(path=str(chroma_path))
        elif chromadb_client is None:
            db_path = Path(__file__).parent.parent.parent / ".chroma"
            chroma_path = Path(db_path)
            chroma_path.mkdir(parents=True, exist_ok=True)
            chromadb_client = chromadb.PersistentClient(path=str(chroma_path))
        collection = chromadb_client.get_collection(name=collection_name)
        count = collection.count()

        # Get all documents
        all_docs = list(collection.get()["documents"])

        domain_counts = {}
        titles = set()

        for doc_data in all_docs:
            domain = doc_data.get("domain", "unknown")
            title = doc_data.get("title", "")

            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if title:
                titles.add(title)

        return {
            "collection_name": collection_name,
            "document_count": count,
            "domain_distribution": domain_counts,
            "unique_titles": len(titles),
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Load secrets
    secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
    else:
        secrets = {}

    print("=" * 60)
    print("🧬 Crawl4AI RAG Database Builder")
    print("=" * 60)

    import argparse

    parser = argparse.ArgumentParser(description="Crawl4AI RAG Database Builder")
    parser.add_argument("--build", action="store_true", help="Build RAG database from URLs")
    parser.add_argument("--query", type=str, help="Query the RAG database")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--urls", type=str, help="Comma-separated list of URLs to crawl")
    parser.add_argument("--collection", type=str, default="web_content", help="Collection name")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size for embedding")
    parser.add_argument("--domain", type=str, help="Filter results by domain")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to return")
    parser.add_argument("--db-path", type=str, default=".chroma", help="Database path")

    args = parser.parse_args()

    # Create ChromaDB client
    chroma_path = Path(args.db_path)
    chroma_path.mkdir(parents=True, exist_ok=True)
    chromadb_client = chromadb.PersistentClient(path=str(chroma_path))

    try:
        if args.stats:
            stats = get_statistics(chromadb_client, collection_name=args.collection)
            print("\n📊 Database Statistics:")
            print(json.dumps(stats, indent=2))

        elif args.query:
            results = query_rag(
                question=args.query,
                chromadb_client=chromadb_client,
                collection_name=args.collection,
                top_k=args.top_k,
                filter_domain=args.domain,
            )

            if results:
                print(f"\n🔍 Query: {args.query}")
                print("=" * 60)
                for i, result in enumerate(results, 1):
                    print(f"\n📄 Result {i} (score: {result['score']:.3f}):")
                    print(f"🔗 Source: {result['source']}")
                    print(f"📑 Domain: {result['domain']}")
                    print(f"📝 Title: {result['title']}")
                    print("\n" + "-" * 40 + "\n")
                    print(result["answer"])
            else:
                print("⚠️  No results found matching the query.")

        elif args.build:
            # Parse URLs
            url_str = args.urls
            if url_str:
                urls = [url.strip() for url in url_str.split(",")]
            else:
                # Default URLs
                urls = [
                    "https://en.wikipedia.org/wiki/Artificial_intelligence",
                    "https://www.nfl.com/",
                    "https://weather.com/",
                ]

            print(f"\n📂 Building RAG database with collection name: {args.collection}")
            print(f"📂 URLs to crawl: {len(urls)}")
            print("-" * 60)

            # Create database
            create_rag_database(
                collection_name=args.collection,
                chunk_size=args.chunk_size,
                verbose=True,
            )

            # Crawl and index
            results = crawl_and_index_pages(
                urls=urls,
                chromadb_client=chromadb_client,
                collection_name=args.collection,
                chunk_size=args.chunk_size,
                verbose=True,
            )

            # Summary
            total_chunks = sum(results.values())
            print("\n" + "=" * 60)
            print("🎉 RAG Database Build Complete!")
            print("=" * 60)
            print(f"✅ Total chunks indexed: {total_chunks}")
            print(f"✅ Collection: {args.collection}")
            print(f"📂 Database path: {args.db_path}/{args.collection}")
            print("\n📋 Usage examples:")
            print(f'  Query: python rag_database.py --query "What is AI?" --collection {args.collection}')
            print(f'  Stats: python rag_database.py --stats --collection {args.collection}')

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        chromadb_client.close()
