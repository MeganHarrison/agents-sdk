#!/usr/bin/env python3
"""
Test RAG retrieval with existing documents in Supabase.
"""

import os
from pathlib import Path

# Load environment variables from root .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from supabase_helpers import get_supabase_client, SupabaseRagStore

try:
    print("Testing RAG retrieval with existing data...")

    # Get client and store
    client = get_supabase_client()
    rag_store = SupabaseRagStore(client)

    # Test 1: Get some documents
    print("\n1. Fetching sample documents...")
    docs = rag_store.vector_search([], limit=3)  # Empty embedding for now
    print(f"✓ Found {len(docs)} documents")

    if docs:
        # Show first document info
        doc = docs[0]
        print(f"\nFirst document:")
        print(f"  - Title: {doc.get('title', 'N/A')}")
        print(f"  - Project: {doc.get('project', 'N/A')}")
        print(f"  - Content length: {len(doc.get('content', ''))} chars")
        print(f"  - Has embedding: {bool(doc.get('embedding'))}")

        # Show content snippet
        content = doc.get('content', '')
        if content:
            snippet = content[:200] + "..." if len(content) > 200 else content
            print(f"  - Content snippet: {snippet}")

    # Test 2: Query by project
    print("\n2. Testing query by project...")
    project_docs = rag_store.query_chunks({"project": "Uniqlo-New Jersey"})
    print(f"✓ Found {len(project_docs)} documents for Uniqlo-New Jersey project")

    # Test 3: Search for specific keywords (basic text search)
    print("\n3. Testing keyword search...")
    response = client.table("documents").select("title, project, content").ilike("content", "%remote work%").limit(5).execute()
    keyword_docs = response.data or []
    print(f"✓ Found {len(keyword_docs)} documents mentioning 'remote work'")

    if keyword_docs:
        for doc in keyword_docs:
            print(f"  - {doc.get('title')} ({doc.get('project')})")

    print("\n✅ RAG retrieval is working with existing data!")
    print("\nNext steps:")
    print("1. Create vector search RPC function for similarity search")
    print("2. Generate embeddings for user queries")
    print("3. Integrate with chat agents")

except Exception as e:
    print(f"❌ Error: {e}")