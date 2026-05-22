"""Test script for rag_database.py"""
import shutil
import sys
sys.path.insert(0, ".")
from mcp_server.tools.rag_database import (
    create_rag_database,
    crawl_and_index_pages,
    query_rag,
    get_statistics,
)


def test_rag_database():
    """Test the RAG database functionality."""
    print("=" * 60)
    print("Testing RAG Database")
    print("=" * 60)

    # Test 1: Create RAG database
    print("\n1. Creating RAG database...")
    db_path = ".chroma_test"
    metadata = create_rag_database(db_path=db_path, chunk_size=500)
    print(f"   ✓ Created database at: {db_path}")
    shutil.rmtree(".chroma_test")
    print(f"   ✓ Database cleaned up")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_rag_database()
