#!/usr/bin/env python3
"""
Simple test to verify the RAG system works before running Streamlit.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_rag_system():
    """Test the RAG system with a simple query."""
    
    try:
        # Import and test
        from barn import Barn
        
        print("✅ Barn imported successfully!")
        
        # Initialize with data
        data_path = "data/pb&j_20250626_173624/final_output.json"
        barn = Barn(data_path=data_path)
        
        print("✅ Barn initialized successfully!")
        
        # Test a simple query
        response = barn.query("What tables are available?")
        
        print("✅ Query executed successfully!")
        print(f"📝 Answer: {response.answer[:200]}...")
        print(f"🔧 Tools used: {response.context.tools_used}")
        print(f"📊 Confidence: {response.context.confidence_score:.2f}")
        
        print("\n🎉 RAG system is working!")
        print("💡 You can now run the Streamlit app with:")
        print("   python3 run_app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_system()
    sys.exit(0 if success else 1) 