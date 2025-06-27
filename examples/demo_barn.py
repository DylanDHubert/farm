#!/usr/bin/env python3
"""
Demo script for the Barn RAG Agent

This script demonstrates how to use the Barn class to create conversational
queries against PB&J pipeline data. The Barn provides a high-level interface
for asking questions and getting intelligent responses based on retrieved context.

Example Usage:
    python demo_barn.py
"""

import json
import os
from src.barn import Barn


def demo_barn_queries():
    """Demonstrate various Barn query capabilities."""
    
    print("🌾 Barn RAG Agent Demo")
    print("=" * 50)
    
    # Initialize Barn with PB&J data
    barn = Barn("data/pb&j_20250626_173624/final_output.json")
    
    print(f"📚 Loaded documents: {barn.get_available_documents()}")
    print()
    
    # Demo queries
    queries = [
        "What are the main ingredients in peanut butter?",
        "Show me compatibility information for bread types",
        "What are the nutritional values?",
        "Tell me about storage recommendations",
        "What equipment do I need to make a sandwich?",
        "How do I measure ingredients properly?"
    ]
    
    for i, question in enumerate(queries, 1):
        print(f"🤔 Query {i}: {question}")
        print("-" * 40)
        
        try:
            # Get response from Barn
            response = barn.query(question, search_type="hybrid")
            
            # Display answer
            print(f"💬 Answer: {response.answer}")
            print()
            
            # Display context information
            print(f"📊 Context:")
            print(f"  - Search method: {response.context.search_method}")
            print(f"  - Confidence: {response.context.confidence_score:.2f}")
            print(f"  - Documents: {response.context.document_ids}")
            print(f"  - Sources found: {len(response.sources)}")
            
            # Show sources
            if response.sources:
                print("  📍 Sources:")
                for source in response.sources[:3]:  # Limit to 3 sources
                    source_type = source.get("type", "unknown")
                    if source_type == "table":
                        print(f"    - Table: {source.get('name', 'Unknown')} (Doc: {source.get('document_id', 'Unknown')})")
                    elif source_type == "content":
                        print(f"    - Page {source.get('page_number', 'Unknown')} (Doc: {source.get('document_id', 'Unknown')})")
            
            print()
            print("=" * 50)
            print()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()
    
    # Demo with different search types
    print("🔍 Search Type Comparison")
    print("=" * 50)
    
    test_question = "What are the ingredients?"
    
    for search_type in ["keyword", "table", "hybrid"]:
        print(f"🔎 {search_type.upper()} search:")
        try:
            response = barn.query(test_question, search_type=search_type)
            print(f"   Answer: {response.answer[:100]}...")
            print(f"   Sources: {len(response.sources)}")
            print()
        except Exception as e:
            print(f"   Error: {str(e)}")
            print()


def demo_barn_with_openai():
    """Demonstrate Barn with OpenAI integration."""
    
    print("🤖 Barn with OpenAI Integration Demo")
    print("=" * 50)
    
    # Initialize Barn
    barn = Barn("data/pb&j_20250626_173624/final_output.json")
    
    # Set a custom prompt template
    custom_prompt = """You are a helpful cooking assistant specializing in PB&J sandwiches.

Context Information:
{context}

User Question: {question}

Please provide a clear, helpful answer based on the context. If you're referencing specific data, mention the source (table name, page number, document). Be conversational and practical.

Answer:"""
    
    barn.set_prompt_template(custom_prompt)
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY environment variable to test OpenAI integration.")
        print("   Using fallback response instead.")
        print()
        
        # Demo fallback response
    question = "What's the best way to store peanut butter and jelly?"
    print(f"🤔 Question: {question}")
    print("-" * 40)
    
    try:
        response = barn.query(question)
        print(f"💬 Answer: {response.answer}")
        print(f"📊 Metadata: {response.metadata}")
        print()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
            print()
        
        return
    
    # Set up OpenAI client
    try:
        barn.set_llm_client(api_key, model="gpt-3.5-turbo")
        print("✅ OpenAI client configured successfully!")
        print()
        
        # Demo OpenAI-powered queries
        openai_questions = [
            "What's the best way to store peanut butter and jelly?",
            "Can you explain the nutritional benefits of this sandwich?",
            "What equipment would I need to make this sandwich properly?",
            "Are there any safety considerations when making PB&J?"
        ]
        
        for i, question in enumerate(openai_questions, 1):
            print(f"🤖 OpenAI Query {i}: {question}")
            print("-" * 50)
            
            try:
                response = barn.query(question)
                print(f"💬 Answer: {response.answer}")
                print()
                print(f"📊 Context:")
                print(f"  - Confidence: {response.context.confidence_score:.2f}")
                print(f"  - Sources: {len(response.sources)}")
                print(f"  - Has LLM: {response.metadata.get('has_llm', False)}")
                print()
                print("=" * 50)
                print()
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print()
                
    except Exception as e:
        print(f"❌ Error setting up OpenAI client: {str(e)}")
        print()


def demo_barn_data_access():
    """Demonstrate Barn's data access capabilities."""
    
    print("📊 Barn Data Access Demo")
    print("=" * 50)
    
    barn = Barn("data/pb&j_20250626_173624/final_output.json")
    
    # Get data overview
    overview = barn.get_data_overview()
    
    print("📈 Data Overview:")
    print(f"  - Total documents: {overview.get('total_documents', 0)}")
    print(f"  - Total pages: {overview.get('total_pages', 0)}")
    print(f"  - Total tables: {overview.get('total_tables', 0)}")
    print(f"  - Total keywords: {overview.get('total_keywords', 0)}")
    print()
    
    # Show document details
    documents = overview.get("documents", {})
    for doc_id, doc_info in documents.items():
        print(f"📄 Document: {doc_id}")
        if hasattr(doc_info, 'page_count'):
            print(f"   - Pages: {doc_info.page_count}")
        if hasattr(doc_info, 'table_count'):
            print(f"   - Tables: {doc_info.table_count}")
        if hasattr(doc_info, 'keyword_count'):
            print(f"   - Keywords: {doc_info.keyword_count}")
        print()


if __name__ == "__main__":
    print("🚀 Starting Barn RAG Agent Demo")
    print()
    
    # Run demos
    demo_barn_queries()
    demo_barn_with_openai()
    demo_barn_data_access()
    
    print("✅ Demo completed!")
    print()
    print("💡 Key Features Demonstrated:")
    print("  - Conversational query interface")
    print("  - Hybrid search (keyword + table)")
    print("  - Structured response format")
    print("  - Source attribution")
    print("  - Configurable prompt templates")
    print("  - OpenAI integration")
    print("  - Data overview access")
    print()
    print("🔧 Next Steps:")
    print("  - Set OPENAI_API_KEY environment variable for full LLM integration")
    print("  - Customize prompt templates for your domain")
    print("  - Add more sophisticated context retrieval")
    print("  - Implement response caching") 