#!/usr/bin/env python3
"""
Debug script to test function calling in the Barn RAG system.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from barn import Barn

def test_function_calling():
    """Test the function calling mechanism."""
    
    # Load the Barn system
    data_path = project_root / "data" / "pb&j_20250626_173624" / "final_output.json"
    barn = Barn(data_path=str(data_path))
    
    # Check if LLM is configured
    if not barn.llm_client:
        print("❌ LLM client not configured")
        return
    
    print("✅ LLM client configured")
    
    # Get available tools
    tools = barn.get_tools_for_function_calling()
    print(f"📋 Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['function']['name']}: {tool['function']['description']}")
    
    # Test a simple query
    question = "How many ounces of bacon are needed for a large BLT sandwich?"
    print(f"\n🔍 Testing query: {question}")
    
    try:
        # Test the multi-step query directly
        print("\n1️⃣ Testing multi-step query...")
        response = barn.query(question)
        print(f"   Steps taken: {response.metadata.get('steps_taken', 0)}")
        print(f"   Tools used: {response.context.tools_used}")
        print(f"   Answer: {response.answer[:200]}...")
        print(f"   Confidence: {response.context.confidence_score}")
        
        # Show detailed tool calls
        print("\n2️⃣ Tool Call Details:")
        for i, call in enumerate(response.metadata.get('tool_calls', [])):
            print(f"   Step {i+1}: {call['tool_name']} with params: {call['parameters']}")
        
        # Show context data
        print("\n3️⃣ Context Data Keys:")
        context_keys = list(response.context.retrieved_data.get('results', {}).keys())
        for key in context_keys:
            print(f"   - {key}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_function_calling() 