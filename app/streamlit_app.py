import streamlit as st
import sys
import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now we can import our modules directly (since PYTHONPATH=src)
from barn import Barn
from models.table import TableInfo, TableRow
from models.search import SearchResult

# Page config
st.set_page_config(
    page_title="PB&J RAG System",
    page_icon="🥪",
    layout="wide"
)

# Title and description
st.title("🥪 PB&J RAG System")
st.markdown("Test the local query system with your document data")

# Initialize Barn
@st.cache_resource
def load_barn():
    """Load the Barn RAG system with data."""
    try:
        logger.info("Loading Barn system...")
        # Use absolute path from project root
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "pb&j_20250626_173624" / "final_output.json"
        logger.info(f"Data path: {data_path}")
        
        barn = Barn(data_path=str(data_path))
        logger.info("Barn system loaded successfully")
        return barn
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        st.error(f"Error loading data: {e}")
        return None

# Load the system
barn = load_barn()

if barn is None:
    st.error("Failed to load the RAG system. Please check your data path.")
    st.stop()

# LLM Configuration Section
with st.sidebar:
    st.header("🤖 LLM Configuration")
    
    # Check if LLM is already configured
    if barn.llm_client:
        st.success("✅ LLM client configured")
        st.info("Function calling is enabled - the agent will intelligently choose tools!")
        
        # Show auto-configuration info
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your-openai-api-key-here":
            st.info("🔧 Auto-configured from .env file")
    else:
        st.error("❌ LLM client required")
        st.info("The agent requires an LLM to function. Please configure one below or set OPENAI_API_KEY in .env file.")
        
        # LLM setup
        with st.expander("🔧 Configure LLM (Required)"):
            api_key = st.text_input(
                "OpenAI API Key:",
                type="password",
                help="Enter your OpenAI API key to enable intelligent function calling"
            )
            
            model = st.selectbox(
                "Model:",
                ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                help="Choose the OpenAI model to use"
            )
            
            if st.button("🚀 Enable Function Calling", type="primary"):
                if api_key:
                    try:
                        barn.set_llm_client(api_key, model)
                        st.success("✅ LLM client configured successfully!")
                        st.rerun()  # Refresh the page to show updated status
                    except Exception as e:
                        st.error(f"❌ Error configuring LLM: {e}")
                        if "invalid_api_key" in str(e) or "401" in str(e):
                            st.error("🔑 **Invalid API Key** - Please check your OpenAI API key and try again.")
                            st.info("💡 **Tips:**")
                            st.info("- Make sure you copied the full API key")
                            st.info("- Check that your OpenAI account has credits")
                            st.info("- Verify the key at https://platform.openai.com/account/api-keys")
                else:
                    st.error("Please enter your OpenAI API key")
            
            # Add option to clear LLM client if there's an error
            if barn.llm_client:
                if st.button("🔄 Reset LLM Client"):
                    barn.clear_llm_client()
                    st.success("✅ LLM client reset. Please reconfigure.")
                    st.rerun()

# Sidebar for system info
with st.sidebar:
    st.header("System Info")
    
    # Get data overview
    overview = barn.get_data_overview()
    if overview and 'statistics' in overview:
        stats = overview['statistics']
        st.metric("Documents", stats.get('total_documents', 0))
        st.metric("Pages", stats.get('total_pages', 0))
        st.metric("Tables", stats.get('total_tables', 0))
        st.metric("Keywords", stats.get('total_keywords', 0))
    
    # Show available tools
    st.header("Available Tools")
    tools = barn.get_tools_for_function_calling()
    for tool in tools[:5]:  # Show first 5 tools
        st.text(f"• {tool['function']['name']}")
    if len(tools) > 5:
        st.text(f"... and {len(tools) - 5} more")

# Main query interface
st.header("Query Interface")

# Show current mode
if barn.llm_client:
    st.success("🤖 **Function Calling Mode** - The agent will intelligently analyze your question and choose the most relevant tools with specific parameters.")
else:
    st.error("❌ **LLM Required** - Please configure an LLM in the sidebar to enable intelligent function calling.")

# Query input
query = st.text_input(
    "Ask a question about your documents:",
    placeholder="e.g., What are the compatibility issues with peanut butter?",
    disabled=not barn.llm_client
)

# Submit button
if st.button("🔍 Ask Question", type="primary"):
    if query.strip():
        with st.spinner("Thinking..."):
            try:
                logger.info(f"Processing query: {query}")
                
                # Let the agent decide what tools to use - no hardcoded search types!
                response = barn.query(query)
                
                logger.info(f"Query completed. Tools used: {response.context.tools_used}")
                logger.info(f"Confidence score: {response.context.confidence_score}")
                logger.info(f"Search method: {response.context.search_method}")
                
                # Display results
                st.success("Analysis complete!")
                
                # Show the answer
                st.subheader("Answer")
                st.write(response.answer)
                
                # Show context information
                with st.expander("🔍 Agent's Reasoning"):
                    st.write(f"**Tools Used:** {', '.join(response.context.tools_used)}")
                    st.write(f"**Confidence:** {response.context.confidence_score:.2f}")
                    st.write(f"**Search Method:** {response.context.search_method}")
                    
                    # Show retrieved data overview
                    if response.context.retrieved_data.get('overview'):
                        st.write("**Data Overview:**")
                        st.json(response.context.retrieved_data['overview'])
                
                # Show detailed debug information
                with st.expander("🐛 Debug Information"):
                    st.write("**Tool Calls Made:**")
                    if "tool_calls" in response.metadata:
                        for i, call in enumerate(response.metadata["tool_calls"]):
                            st.write(f"**Call {i+1}:**")
                            st.write(f"  - Tool: `{call['tool_name']}`")
                            st.write(f"  - Parameters: `{json.dumps(call['parameters'], indent=2)}`")
                    
                    st.write("**Raw Results:**")
                    results = response.context.retrieved_data.get("results", {})
                    for tool_name, result in results.items():
                        st.write(f"**{tool_name}:**")
                        if isinstance(result, dict) and "parameters" in result:
                            st.write(f"  - Parameters: {result['parameters']}")
                            if "result" in result:
                                st.write(f"  - Result: {json.dumps(result['result'], indent=2, default=str)}")
                            if "error" in result:
                                st.write(f"  - Error: {result['error']}")
                        else:
                            st.write(f"  - {json.dumps(result, indent=2, default=str)}")
                    
                    st.write("**Full Metadata:**")
                    st.json(response.metadata)
                
                # Show sources
                if response.sources:
                    st.subheader("📚 Sources")
                    for i, source in enumerate(response.sources[:5]):  # Show first 5 sources
                        with st.expander(f"Source {i+1}: {source.get('tool', 'Unknown')}"):
                            st.write(f"**Type:** {source.get('type', 'Unknown')}")
                            st.write(f"**Score:** {source.get('score', 0):.2f}")
                            if 'page' in source:
                                st.write(f"**Page:** {source['page']}")
                            if 'context' in source:
                                st.write(f"**Context:** {source['context']}")
                
                # Show metadata
                with st.expander("📊 Response Metadata"):
                    st.json(response.metadata)
                    
            except Exception as e:
                logger.error(f"Error during analysis: {e}", exc_info=True)
                st.error(f"Error during analysis: {e}")
                st.exception(e)
    else:
        st.warning("Please enter a question.")

# Tool testing section
st.header("🔧 Tool Testing")

# Tool selection
available_tools = list(barn.tools.keys())
selected_tool = st.selectbox("Select a tool to test:", available_tools)

if selected_tool:
    tool_def = barn.tools[selected_tool]
    st.write(f"**Description:** {tool_def.description}")
    
    # Show parameters
    if tool_def.parameters.get('properties'):
        st.write("**Parameters:**")
        for param_name, param_info in tool_def.parameters['properties'].items():
            required = param_name in tool_def.parameters.get('required', [])
            st.write(f"• `{param_name}`: {param_info.get('type', 'unknown')} {param_info.get('description', '')} {'(required)' if required else '(optional)'}")
    
    # Test the tool
    if st.button(f"Test {selected_tool}"):
        try:
            # For now, just call tools that don't need parameters
            if selected_tool in ["get_table_catalog", "get_compatibility_tables", "get_measurement_tables", "get_available_keywords", "get_data_overview"]:
                result = barn.call_tool(selected_tool)
                st.success(f"Tool executed successfully!")
                st.json(result)
            else:
                st.info(f"Tool '{selected_tool}' requires parameters. Use the query interface above to test it.")
        except Exception as e:
            st.error(f"Error testing tool: {e}")

# Footer
st.markdown("---")
st.markdown("*Built with PB&J RAG System*") 