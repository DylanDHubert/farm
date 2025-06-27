import streamlit as st
import sys
import os
from pathlib import Path

# Set up the environment properly
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

# Page config
st.set_page_config(
    page_title="PB&J RAG System",
    page_icon="🥪",
    layout="wide"
)

# Title
st.title("🥪 PB&J RAG System - Quick Test")
st.markdown("Testing the local query system")

# Simple test function
def test_rag_system():
    """Test the RAG system with a simple query."""
    try:
        # Import after setting up the path
        from barn import Barn
        
        # Initialize with data
        data_path = "data/pb&j_20250626_173624/final_output.json"
        barn = Barn(data_path=data_path)
        
        # Test query
        query = "What tables are available?"
        response = barn.query(query)
        
        return barn, response
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

# Test the system
if st.button("🔍 Test RAG System", type="primary"):
    with st.spinner("Testing..."):
        barn, response = test_rag_system()
        
        if barn and response:
            st.success("✅ RAG System is working!")
            
            # Show results
            st.subheader("Test Results")
            st.write(f"**Query:** What tables are available?")
            st.write(f"**Answer:** {response.answer}")
            st.write(f"**Tools Used:** {', '.join(response.context.tools_used)}")
            st.write(f"**Confidence:** {response.context.confidence_score:.2f}")
            
            # Show system info
            st.subheader("System Info")
            overview = barn.get_data_overview()
            if overview and 'statistics' in overview:
                stats = overview['statistics']
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Documents", stats.get('total_documents', 0))
                with col2:
                    st.metric("Pages", stats.get('total_pages', 0))
                with col3:
                    st.metric("Tables", stats.get('total_tables', 0))
                with col4:
                    st.metric("Keywords", stats.get('total_keywords', 0))
            
            # Show available tools
            st.subheader("Available Tools")
            tools = list(barn.tools.keys())
            st.write(f"Found {len(tools)} tools:")
            for tool in tools[:10]:  # Show first 10
                st.write(f"• {tool}")
            if len(tools) > 10:
                st.write(f"... and {len(tools) - 10} more")
                
        else:
            st.error("❌ RAG System failed to load")

# Simple query interface
st.header("Simple Query Test")
query = st.text_input("Ask a question:", placeholder="e.g., What are the compatibility issues?")

if st.button("🔍 Ask", type="secondary") and query:
    with st.spinner("Searching..."):
        try:
            barn, response = test_rag_system()
            if barn:
                response = barn.query(query)
                st.write(f"**Answer:** {response.answer}")
                st.write(f"**Confidence:** {response.context.confidence_score:.2f}")
        except Exception as e:
            st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("*Simple PB&J RAG Test*") 