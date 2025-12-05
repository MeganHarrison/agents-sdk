#!/usr/bin/env python3
"""
Check the schema of the documents table in Supabase.
"""

import os
import sys
from pathlib import Path

# Load environment variables from root .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from supabase_helpers import get_supabase_client

try:
    print("Checking documents table schema...")

    # Get client
    client = get_supabase_client()

    # Get a sample row to see the columns
    response = client.table("documents").select("*").limit(1).execute()

    if response.data and len(response.data) > 0:
        print("\n✅ Documents table exists with columns:")
        for key in response.data[0].keys():
            print(f"  - {key}: {type(response.data[0][key]).__name__}")
        print(f"\nSample row:")
        print(response.data[0])
    else:
        print("\n⚠️  Documents table exists but is empty")
        # Try to get table info via raw SQL
        result = client.rpc("get_table_columns", {"table_name": "documents"}).execute()
        if result.data:
            print("Table columns from schema:")
            for col in result.data:
                print(f"  - {col}")
        else:
            print("Could not retrieve table schema")

except Exception as e:
    print(f"❌ Error: {e}")
    # Try alternative method to get schema
    print("\nAttempting to query with empty filter to see structure...")
    try:
        response = client.table("documents").select("*").eq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("Query succeeded, table exists")
    except Exception as e2:
        print(f"Query error details: {e2}")