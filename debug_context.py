#!/usr/bin/env python3
"""
Debug script to examine context retrieval in the Barn RAG system
"""

import os
import json
from src.barn import Barn

def debug_context_retrieval():
    """Debug the context retrieval process."""
    
    print("🔍 Debugging Context Retrieval")
    print("=" * 50)
    
    # Load environment variables
    export_output = os.popen('cat .env | xargs').read().strip()
    for line in export_output.split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value
    
    # Initialize Barn
    barn = Barn("data/pb&j_20250626_173624/final_output.json")
    
    # Set up OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        barn.set_llm_client(api_key, model="gpt-3.5-turbo")
        print("✅ OpenAI client configured")
    else:
        print("❌ No OpenAI API key found")
        return
    
    # Test queries with detailed context inspection
    test_queries = [
        "How many ounces of bacon are needed for a large sandwich?",
        "Can I put Mustard on a Club Sandwich?",
        "Explain bread in the context of software development."
    ]
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {question}")
        print("-" * 50)
        
        # Get the raw context data
        context_data = barn._retrieve_context_with_tools(question, ["pitchfork", "sickle"])
        
        print("📊 Raw Context Data:")
        print(f"  - Document IDs: {context_data.get('document_ids', [])}")
        print(f"  - Confidence: {context_data.get('confidence', 0.0)}")
        print(f"  - Tables found: {len(context_data.get('tables', []))}")
        print(f"  - Keywords found: {len(context_data.get('keywords', []))}")
        
        # Examine tables
        if context_data.get('tables'):
            print("\n📋 Tables Found:")
            for j, table in enumerate(context_data['tables'], 1):
                print(f"  Table {j}:")
                print(f"    - Name: {table.get('table_name', 'Unknown')}")
                print(f"    - Doc ID: {table.get('doc_id', 'Unknown')}")
                print(f"    - Data keys: {list(table.keys())}")
                if 'data' in table:
                    print(f"    - Data type: {type(table['data'])}")
                    if isinstance(table['data'], list) and len(table['data']) > 0:
                        print(f"    - First row: {table['data'][0]}")
                    else:
                        print(f"    - Data content: {str(table['data'])[:200]}...")
                print()
        else:
            print("\n❌ No tables found!")
        
        # Examine keywords
        if context_data.get('keywords'):
            print("🔑 Keywords Found:")
            for j, result in enumerate(context_data['keywords'][:3], 1):  # Limit to 3
                print(f"  Result {j}:")
                print(f"    - Page: {getattr(result, 'page_number', 'Unknown')}")
                print(f"    - Doc ID: {getattr(result, 'doc_id', 'Unknown')}")
                print(f"    - Context: {getattr(result, 'context', 'Unknown')[:100]}...")
                print()
        else:
            print("❌ No keywords found!")
        
        # Show formatted context that would be sent to LLM
        formatted_context = barn._format_context_for_llm(context_data)
        print("📝 Formatted Context for LLM:")
        print("-" * 30)
        print(formatted_context[:1000] + "..." if len(formatted_context) > 1000 else formatted_context)
        print("-" * 30)
        
        # Test the actual LLM response
        print("\n🤖 LLM Response:")
        try:
            response = barn.query(question, search_type="hybrid")
            print(f"Answer: {response.answer}")
            print(f"Sources: {len(response.sources)}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("\n" + "="*50)

def debug_farmer_data():
    """Debug the Farmer's data access capabilities."""
    
    print("\n🔧 Debugging Farmer Data Access")
    print("=" * 50)
    
    from src.farmer import Farmer
    
    farmer = Farmer()
    farmer.load_document("default", "data/pb&j_20250626_173624/final_output.json")
    
    # Check data overview
    overview = farmer.get_data_overview()
    print("📊 Data Overview:")
    print(json.dumps(overview, indent=2))
    
    # Check table catalog
    print("\n📋 Table Catalog:")
    try:
        table_catalog = farmer.get_table_catalog()
        for table in table_catalog:
            print(f"  - {table.title} (ID: {table.table_id})")
    except Exception as e:
        print(f"Error getting table catalog: {e}")
    
    # Check keyword search
    print("\n🔍 Testing Keyword Search:")
    try:
        results = farmer.search("peanut butter", search_type="all")
        print(f"Found {len(results)} results for 'peanut butter'")
        for i, result in enumerate(results[:3], 1):
            print(f"  Result {i}: Page {getattr(result, 'page_number', 'Unknown')}")
            print(f"    Context: {getattr(result, 'context', 'Unknown')[:100]}...")
    except Exception as e:
        print(f"Error in keyword search: {e}")

if __name__ == "__main__":
    debug_context_retrieval()
    debug_farmer_data() 