#!/usr/bin/env python3
"""
Simple test script to verify the Streamlit app can import and run.
Run this from the project root directory.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    # Test imports
    from barn import Barn
    from models.table import TableInfo, TableRow
    from models.search import SearchResult
    
    print("✅ All imports successful!")
    
    # Test Barn initialization
    data_path = "data/pb&j_20250626_173624/final_output.json"
    barn = Barn(data_path=data_path)
    print("✅ Barn initialized successfully!")
    
    # Test a simple query
    response = barn.query("What tables are available?")
    print("✅ Query executed successfully!")
    print(f"Answer: {response.answer[:100]}...")
    
    print("\n🎉 App is ready to run!")
    print("Run: cd app && streamlit run streamlit_app.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 