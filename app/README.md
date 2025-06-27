# PB&J RAG System - Streamlit App

A simple Streamlit interface to test the PB&J RAG system locally.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the data file in the correct location:
```
data/pb&j_20250626_173624/final_output.json
```

## Running the App

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Features

- **Query Interface**: Ask questions about your documents
- **System Info**: View statistics about your data
- **Tool Testing**: Test individual tools in the system
- **Search Results**: View detailed search results and sources

## Example Queries

- "What are the compatibility issues with peanut butter?"
- "Show me all tables"
- "What pages mention jelly?"
- "What are the nutrition facts?" 