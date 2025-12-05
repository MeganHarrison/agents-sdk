#!/usr/bin/env python3
"""
Test script to verify RAG setup is working correctly.
Loads environment variables from .env file and verifies configuration.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

# Load environment variables from root .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
print(f"Loaded environment from: {env_path}")

def check_environment() -> Dict[str, bool]:
    """Check if required environment variables are set."""
    checks = {
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "SUPABASE_URL": bool(os.environ.get("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(os.environ.get("SUPABASE_ANON_KEY")),
    }
    return checks

def test_imports() -> bool:
    """Test if all required modules can be imported."""
    try:
        print("Testing imports...")

        # Test OpenAI SDK
        from openai import AsyncOpenAI
        print("✓ OpenAI SDK imported")

        # Test agents SDK
        from agents import Agent, Runner
        print("✓ Agents SDK imported")

        # Test Alleato workflow
        from alleato_agent_workflow.alleato_agent_workflow import (
            run_workflow,
            WorkflowInput,
            classification_agent,
            project,
            internal_knowledge_base,
            strategist
        )
        print("✓ Alleato workflow imported")

        # Test FastAPI
        from fastapi import FastAPI
        print("✓ FastAPI imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

async def test_basic_workflow():
    """Test basic workflow execution."""
    try:
        print("\nTesting basic workflow...")
        from alleato_agent_workflow.alleato_agent_workflow import run_workflow, WorkflowInput

        # Test with a simple query
        test_input = WorkflowInput(input_as_text="What is our remote work policy?")

        print("Running workflow with test query...")
        result = await run_workflow(test_input)

        if result:
            print("✓ Workflow executed successfully")
            print(f"Result type: {type(result)}")
            return True
        else:
            print("✗ Workflow returned empty result")
            return False

    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("RAG Setup Test Script")
    print("=" * 60)

    # Check environment variables
    print("\n1. Checking environment variables...")
    env_checks = check_environment()
    all_env_set = all(env_checks.values())

    for var, is_set in env_checks.items():
        status = "✓" if is_set else "✗"
        print(f"  {status} {var}: {'Set' if is_set else 'Not set'}")

    if not all_env_set:
        print("\n⚠️  Some environment variables are missing!")
        print("Please set them before running the application:")
        print("  export OPENAI_API_KEY=your_key_here")
        print("  export SUPABASE_URL=your_project_url")
        print("  export SUPABASE_ANON_KEY=your_anon_key")
        if not env_checks["OPENAI_API_KEY"]:
            print("\nSkipping workflow test due to missing OPENAI_API_KEY")
            return

    # Test imports
    print("\n2. Testing module imports...")
    if not test_imports():
        print("\n⚠️  Some imports failed. Please check your installation.")
        return

    # Test workflow (only if API key is set)
    if env_checks["OPENAI_API_KEY"]:
        print("\n3. Testing workflow execution...")
        asyncio.run(test_basic_workflow())
    else:
        print("\n3. Skipping workflow test (no API key)")

    print("\n" + "=" * 60)
    print("Test complete!")

    if all_env_set and test_imports():
        print("\n✅ System is ready for testing!")
        print("\nNext steps:")
        print("1. Start the backend: python -m uvicorn api:app --reload --port 8000")
        print("2. Start the frontend: cd ui && npm run dev")
        print("3. Visit http://localhost:3000/rag-chat")
    else:
        print("\n⚠️  Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()