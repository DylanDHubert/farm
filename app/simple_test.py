#!/usr/bin/env python3
"""
Simple test script that directly tests the RAG system.
This bypasses the import issues by running from the project root.
"""

import sys
import os
from pathlib import Path

# Change to project root and add src to path
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

def test_simple_query():
    """Test a simple query to verify the system works."""
    
    try:
        # Import after setting up the path
        from barn import Barn
        
        print("✅ Barn imported successfully!")
        
        # Test with data
        data_path = "data/pb&j_20250626_173624/final_output.json"
        barn = Barn(data_path=data_path)
        
        print("✅ Barn initialized successfully!")
        
        # Test query
        query = "What tables are available?"
        response = barn.query(query)
        
        print(f"✅ Query: {query}")
        print(f"📝 Answer: {response.answer}")
        print(f"🔧 Tools used: {response.context.tools_used}")
        print(f"📊 Confidence: {response.context.confidence_score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_query()
    if success:
        print("\n🎉 System is working! The issue is with Streamlit imports.")
        print("💡 Try running the app from the project root with:")
        print("   cd /Users/dylanhubert/TEMPORARY\\ NAME")
        print("   PYTHONPATH=src streamlit run app/streamlit_app.py")
    else:
        print("\n❌ System has issues that need to be fixed first.") 