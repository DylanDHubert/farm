#!/usr/bin/env python3
"""
Demo script for the Farm-Themed PB&J Data Tools

This script demonstrates the complete farm ecosystem, showing how all the tools
work together to provide comprehensive data access and search capabilities.

Example Usage:
    python demo_farm.py
"""

import json
from src.farmer import Farmer


def demo_farmer_basics():
    """Demonstrate basic Farmer functionality."""
    
    print("👨‍🌾 Farmer Basics Demo")
    print("=" * 50)
    
    # Initialize the farmer
    farmer = Farmer()
    
    # Load a document
    success = farmer.load_document("pbj_doc", "data/pb&j_20250626_173624/final_output.json")
    print(f"📄 Document loaded: {success}")
    
    if success:
        print(f"✅ Farm ready: {farmer.is_ready()}")
        print()
        
        # Get data overview
        overview = farmer.get_data_overview()
        print("📊 Data Overview:")
        print(f"  - Total documents: {overview.get('total_documents', 0)}")
        print(f"  - Total pages: {overview.get('total_pages', 0)}")
        print(f"  - Total tables: {overview.get('total_tables', 0)}")
        print(f"  - Total keywords: {overview.get('total_keywords', 0)}")
        print()
        
        # Get farm statistics
        stats = farmer.get_farm_stats()
        print("🌾 Farm Statistics:")
        print(f"  - Silo documents: {stats.total_documents}")
        print(f"  - Total pages: {stats.total_pages}")
        print(f"  - Total tables: {stats.total_tables}")
        print(f"  - Total keywords: {stats.total_keywords}")
        print()
    
    return farmer


def demo_sickle_search(farmer):
    """Demonstrate Sickle keyword search capabilities."""
    
    print("🔪 Sickle Search Demo")
    print("=" * 50)
    
    if not farmer.is_ready():
        print("❌ Farm not ready. Load documents first.")
        return
    
    # Search queries
    search_queries = [
        "peanut butter",
        "bread compatibility",
        "nutritional values",
        "storage recommendations"
    ]
    
    for query in search_queries:
        print(f"🔍 Searching for: '{query}'")
        print("-" * 30)
        
        try:
            # Search across all content
            results = farmer.search(query, search_type="all", limit=3)
            
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Page {result.page_number} (Doc: {result.doc_id})")
                print(f"     Title: {result.page_title}")
                print(f"     Score: {result.match_score:.2f}")
                print(f"     Keywords: {result.matched_keywords}")
                print()
            
            print()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()
    
    # Get available keywords
    keywords = farmer.get_available_keywords()
    print(f"📝 Available keywords: {len(keywords)} total")
    print(f"Sample keywords: {keywords[:10]}")
    print()


def demo_pitchfork_tables(farmer):
    """Demonstrate Pitchfork table access capabilities."""
    
    print("🍴 Pitchfork Table Access Demo")
    print("=" * 50)
    
    if not farmer.is_ready():
        print("❌ Farm not ready. Load documents first.")
        return
    
    # Get table catalog
    catalog = farmer.get_table_catalog()
    print(f"📋 Table Catalog: {len(catalog)} tables found")
    print()
    
    # Show table categories
    categories = {}
    for table in catalog:
        category = table.technical_category
        if category not in categories:
            categories[category] = []
        categories[category].append(table.title)
    
    print("📂 Tables by Category:")
    for category, tables in categories.items():
        print(f"  {category}: {len(tables)} tables")
        for table in tables[:3]:  # Show first 3 tables per category
            print(f"    - {table}")
        if len(tables) > 3:
            print(f"    ... and {len(tables) - 3} more")
        print()
    
    # Get specific table types
    compatibility_tables = farmer.get_compatibility_tables()
    nutrition_tables = farmer.get_measurement_tables()
    
    print(f"🔗 Compatibility tables: {len(compatibility_tables)}")
    print(f"📊 Nutrition tables: {len(nutrition_tables)}")
    print()
    
    # Get a specific table
    if catalog:
        table_info = catalog[0]
        print(f"📄 Getting table: {table_info.title}")
        table_data = farmer.get_table_by_id(table_info.table_id)
        
        if table_data:
            print(f"  - Rows: {len(table_data.get('rows', []))}")
            print(f"  - Columns: {len(table_data.get('columns', []))}")
            print(f"  - Category: {table_data.get('metadata', {}).get('technical_category', 'Unknown')}")
            
            # Show first few rows
            rows = table_data.get('rows', [])
            if rows:
                print("  - Sample data:")
                for i, row in enumerate(rows[:3]):
                    print(f"    Row {i+1}: {row}")
                if len(rows) > 3:
                    print(f"    ... and {len(rows) - 3} more rows")
        print()


def demo_hybrid_queries(farmer):
    """Demonstrate hybrid search combining keyword and table search."""
    
    print("🔄 Hybrid Query Demo")
    print("=" * 50)
    
    if not farmer.is_ready():
        print("❌ Farm not ready. Load documents first.")
        return
    
    # Complex queries that benefit from both search types
    hybrid_queries = [
        "What bread types are compatible with peanut butter?",
        "Show me nutritional information for jelly",
        "What equipment do I need for storage?",
        "How do I measure ingredients properly?"
    ]
    
    for query in hybrid_queries:
        print(f"🤔 Query: {query}")
        print("-" * 40)
        
        try:
            # Keyword search
            keyword_results = farmer.search(query, search_type="all", limit=3)
            print(f"🔍 Keyword results: {len(keyword_results)}")
            
            # Table search (using table catalog)
            catalog = farmer.get_table_catalog()
            relevant_tables = []
            query_words = query.lower().split()
            
            for table in catalog:
                if any(word in table.title.lower() for word in query_words):
                    relevant_tables.append(table)
            
            print(f"📋 Relevant tables: {len(relevant_tables)}")
    
            # Show combined results
            if keyword_results:
                print("  📄 Relevant pages:")
                for result in keyword_results[:2]:
                    print(f"    - Page {result.page_number}: {result.page_title}")
            
            if relevant_tables:
                print("  📊 Relevant tables:")
                for table in relevant_tables[:2]:
                    print(f"    - {table.title} ({table.technical_category})")
            
            print()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()


def demo_document_management(farmer):
    """Demonstrate document management capabilities."""
    
    print("📚 Document Management Demo")
    print("=" * 50)
    
    if not farmer.is_ready():
        print("❌ Farm not ready. Load documents first.")
        return
    
    # Get document information
    doc_ids = farmer.get_document_ids()
    print(f"📄 Loaded documents: {doc_ids}")
    print()
    
    for doc_id in doc_ids:
        doc_info = farmer.get_document_info(doc_id)
    if doc_info:
            print(f"📋 Document: {doc_id}")
            print(f"  - Pages: {doc_info.get('page_count', 0)}")
            print(f"  - Tables: {doc_info.get('table_count', 0)}")
            print(f"  - Keywords: {doc_info.get('keyword_count', 0)}")
            print(f"  - File size: {doc_info.get('file_size_mb', 0):.2f} MB")
            print()
    
    # Get all keywords across documents
    all_keywords = farmer.get_all_keywords()
    print(f"📝 Total unique keywords: {len(all_keywords)}")
    print(f"Sample keywords: {all_keywords[:15]}")
    print()


if __name__ == "__main__":
    print("🚀 Starting Farm-Themed PB&J Data Tools Demo")
    print()
    
    # Run demos
    farmer = demo_farmer_basics()
    
    if farmer and farmer.is_ready():
        demo_sickle_search(farmer)
        demo_pitchfork_tables(farmer)
        demo_hybrid_queries(farmer)
        demo_document_management(farmer)
    
    print("✅ Demo completed!")
    print()
    print("💡 Key Features Demonstrated:")
    print("  - Multi-document data loading")
    print("  - Fast keyword search with Sickle")
    print("  - Comprehensive table access with Pitchfork")
    print("  - Hybrid search combining multiple tools")
    print("  - Document management and statistics")
    print("  - Structured data organization")
    print()
    print("🔧 Next Steps:")
    print("  - Load additional documents for comparison")
    print("  - Implement semantic search with Scythe")
    print("  - Add more sophisticated filtering")
    print("  - Integrate with external data sources") 