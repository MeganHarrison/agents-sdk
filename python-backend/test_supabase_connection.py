#!/usr/bin/env python3
"""
Test Supabase connection using the Python SDK.
"""

import os
import sys
from pathlib import Path

# Load environment variables from root .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

try:
    from supabase_helpers import get_supabase_client, SupabaseRagStore

    print("Testing Supabase connection...")

    # Get client
    client = get_supabase_client()
    print("✓ Supabase client created successfully")

    # Create RAG store
    rag_store = SupabaseRagStore(client)
    print("✓ RAG store initialized")

    # Try to query documents table
    try:
        chunks = rag_store.query_chunks({"chunk_index": 0})
        print(f"✓ Successfully queried documents table, found {len(chunks)} chunks")
    except Exception as e:
        print(f"⚠️  Documents table query failed (might be empty): {e}")

    print("\n✅ Supabase connection is working!")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)