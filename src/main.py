#!/usr/bin/env python3
"""
LLM Research Agent - Main Entry Point

Usage:
    python src/main.py "your question here"
"""

import sys
import json
import asyncio
from typing import Dict, Any

from agent.llm_factory import get_llm
from agent.graph import run_agent_sync


def main():
    """Main entry point for the research agent."""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: docker compose run --rm agent \"your question here\"")
        sys.exit(1)
    
    # Get question from command line
    question = " ".join(sys.argv[1:])
    
    print(f"Researching: {question}")
    print("=" * 50)
    
    try:
        # Get LLM
        llm = get_llm()
        
        # Run the agent
        result = run_agent_sync(question, llm)
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            "answer": f"Error: {str(e)}",
            "citations": [],
            "slots": [],
            "filled_slots": [],
            "iterations": 0
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main() 