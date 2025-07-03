import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import get_config_manager, list_datasets
from barn import Barn

st.set_page_config(
    page_title="RAG System",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Retrieval-Augmented Generation (RAG) System")
st.markdown("A domain-agnostic document analysis tool.")

# --- Dataset Selection ---
st.header("1. Select Dataset")
config_manager = get_config_manager()
datasets = list_datasets()

if not datasets:
    st.error("No datasets found in the data/ directory.")
    st.stop()

dataset_names = [d['name'] for d in datasets]
default_idx = next((i for i, d in enumerate(datasets) if d['is_default']), 0)
selected_name = st.selectbox("Choose a dataset to analyze:", dataset_names, index=default_idx)
selected_config = config_manager.get_dataset_config(selected_name)

st.write(f"**Domain:** {selected_config.domain}")
st.write(f"**Description:** {selected_config.description}")
st.write(f"**Pages:** {selected_config.page_count}  |  **Tables:** {selected_config.table_count}  |  **Keywords:** {selected_config.keyword_count}")

# --- Load Barn ---
st.header("2. System Initialization")
with st.spinner("Loading dataset and initializing agent..."):
    barn = Barn(data_path=str(selected_config.path))
    st.success("System loaded successfully!")

# --- LLM Configuration ---
st.header("3. LLM Configuration")

# Try to load API key from .env
import os
from dotenv import load_dotenv
load_dotenv()

env_api_key = os.getenv("OPENAI_API_KEY")
if env_api_key and env_api_key != "your-openai-api-key-here":
    api_key = env_api_key
    st.success("✅ API key loaded from .env file")
else:
    api_key = st.text_input(
        "OpenAI API Key:",
        type="password",
        help="Enter your OpenAI API key to enable intelligent agentic retrieval"
    )

model = st.selectbox(
    "Model:",
    ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
    help="Choose the OpenAI model to use"
)

if api_key:
    try:
        barn.set_llm_client(api_key, model)
        st.success("✅ LLM client configured successfully!")
    except Exception as e:
        st.error(f"❌ Error configuring LLM: {e}")
        st.stop()
else:
    st.warning("⚠️ LLM client required for agentic retrieval. Please enter your API key.")
    st.stop()

# --- Test Agentic Retrieval ---
st.header("4. Test Agentic Retrieval")
def get_default_test_query():
    # Try to generate a generic test query based on keywords
    keywords = barn.call_tool("get_available_keywords")
    if keywords:
        return f"Summarize the key findings about {keywords[0]} in this document."
    return "Summarize the key findings in this document."

default_query = get_default_test_query()
query = st.text_input(
    "Test Query:",
    value=default_query,
    help="This will run a generic agentic retrieval using the selected dataset."
)

if st.button("Run Test Retrieval", type="primary"):
    with st.spinner("Running agentic retrieval..."):
        try:
            response = barn.query(query)
            st.success("Retrieval complete!")
            st.subheader("Answer")
            st.write(response.answer)

            with st.expander("Agent Context & Reasoning"):
                st.write(f"**Tools Used:** {', '.join(response.context.tools_used)}")
                st.write(f"**Confidence:** {response.context.confidence_score:.2f}")
                st.write(f"**Search Method:** {response.context.search_method}")
                st.json(response.context.retrieved_data)

            with st.expander("Debug Metadata"):
                st.json(response.metadata)

            if response.sources:
                st.subheader("Sources")
                for i, source in enumerate(response.sources):
                    st.write(f"{i+1}. {source}")
        except Exception as e:
            st.error(f"Error during retrieval: {e}")

st.markdown("---")
st.markdown("*This app is domain-agnostic and ready for any document dataset.*") 