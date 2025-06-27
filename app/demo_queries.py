#!/usr/bin/env python3
"""
Demo script showing example queries and their results using the PB&J RAG system.
Run this from the project root directory.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from barn import Barn

def demo_queries():
    """Run a series of demo queries to showcase the RAG system."""
    
    print("🥪 PB&J RAG System Demo")
    print("=" * 50)
    
    # Initialize Barn
    data_path = "data/pb&j_20250626_173624/final_output.json"
    barn = Barn(data_path=data_path)
    
    # Demo queries
    queries = [
        "What tables are available?",
        "What are the compatibility issues with peanut butter?",
        "Show me information about jelly",
        "What pages mention sandwiches?",
        "What are the nutrition facts?",
        "Tell me about drink compatibility"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 40)
        
        try:
            response = barn.query(query)
            
            print(f"✅ Answer: {response.answer}")
            print(f"🔧 Tools used: {', '.join(response.context.tools_used)}")
            print(f"📊 Confidence: {response.context.confidence_score:.2f}")
            print(f"📚 Sources: {len(response.sources)} found")
            
            # Show first source
            if response.sources:
                first_source = response.sources[0]
                print(f"📍 Top source: {first_source.get('tool', 'Unknown')} (score: {first_source.get('score', 0):.2f})")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

def demo_tools():
    """Demo individual tools."""
    
    print("\n🔧 Tool Demo")
    print("=" * 30)
    
    # Initialize Barn
    data_path = "data/pb&j_20250626_173624/final_output.json"
    barn = Barn(data_path=data_path)
    
    # Test individual tools
    tools_to_test = [
        "get_table_catalog",
        "get_compatibility_tables", 
        "get_measurement_tables",
        "get_available_keywords",
        "get_data_overview"
    ]
    
    for tool_name in tools_to_test:
        print(f"\n🔧 Testing {tool_name}:")
        try:
            result = barn.call_tool(tool_name)
            if isinstance(result, list):
                print(f"   ✅ Found {len(result)} items")
                if result:
                    print(f"   📝 First item: {str(result[0])[:100]}...")
            elif isinstance(result, dict):
                print(f"   ✅ Success - {len(result)} keys")
            else:
                print(f"   ✅ Result: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    try:
        demo_queries()
        demo_tools()
        print("\n🎉 Demo completed successfully!")
        print("\n💡 To run the Streamlit app:")
        print("   python3 run_app.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 