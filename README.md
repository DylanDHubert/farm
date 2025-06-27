# 🌾 Farm-Themed PB&J Data Tools

A modular, farm-themed architecture for managing and querying structured document data from PB&J pipeline outputs. Built with separation of concerns and extensibility in mind.

## 🏗️ Architecture Overview

The system is organized around a farm metaphor:

- **🌾 Silo**: Base data storage and organization
- **🔪 Sickle**: Fast keyword search (cuts through data like a sickle through wheat)
- **🍴 Pitchfork**: Table access and filtering (organizes data like a pitchfork organizes hay)
- **🌾 Scythe**: Semantic search (future implementation)
- **👨‍🌾 Farmer**: Manager and orchestrator
- **🏠 Barn**: RAG agent for conversational queries

## 📁 File Structure

```
├── silo.py              # Base data storage class
├── sickle.py            # Keyword search engine
├── pitchfork.py         # Table access and filtering
├── scythe.py            # Semantic search (stub)
├── farmer.py            # Manager and orchestrator
├── barn.py              # RAG agent for conversational queries
├── demo_farm.py         # Comprehensive demo script
├── demo_barn.py         # Barn RAG agent demo
└── README.md            # This documentation
```

## 🚀 Quick Start

```python
from farmer import Farmer

# Initialize the farmer
farmer = Farmer()

# Load a document
farmer.load_document("doc_id", "path/to/final_output.json")

# Search for content
results = farmer.search("peanut butter", search_type="all", limit=5)

# Get table catalog
tables = farmer.get_table_catalog()

# Get specific table
table_data = farmer.get_table_by_id("table_1")
```

## 📚 Detailed Documentation

### 🌾 Silo - Base Data Storage

**Purpose**: Standalone data container that loads and organizes structured data from multiple PB&J pipeline outputs.

**Key Features**:
- Multi-document support
- Unified data access
- Document metadata tracking
- No search or retrieval logic (pure data storage)

**Main Methods**:
- `load_document(doc_id, data_path)` - Load single document
- `load_documents(doc_mappings)` - Load multiple documents
- `get_all_pages()` - Get all pages with document context
- `get_all_tables()` - Get all tables with document context
- `get_statistics()` - Get comprehensive data statistics

**Usage**:
```python
from silo import Silo

silo = Silo()
silo.load_document("doc1", "path/to/data.json")
pages = silo.get_all_pages()
tables = silo.get_all_tables()
```

### 🔪 Sickle - Keyword Search Engine

**Purpose**: Fast, efficient keyword-based search across pages, tables, and metadata with support for page-level results and future PDF highlighting.

**Key Features**:
- Fast keyword indexing
- Multiple search types (all, pages, tables, titles)
- Page number support for PDF highlighting
- Keyword-based scoring and ranking
- Context-aware results

**Main Methods**:
- `build_index()` - Build search index from silo data
- `search(query, search_type, limit)` - Search with natural language query
- `search_by_keywords(keywords, search_type, limit)` - Search with specific keywords
- `get_page_by_number(page_number)` - Get page by number for PDF highlighting
- `get_available_keywords()` - Get all indexed keywords

**Usage**:
```python
from sickle import Sickle
from silo import Silo

silo = Silo()
silo.load_document("doc1", "path/to/data.json")

sickle = Sickle(silo)
sickle.build_index()

# Search for content
results = sickle.search("compatibility", search_type="all", limit=5)

# Search by specific keywords
results = sickle.search_by_keywords(["jelly", "jam"], search_type="tables")
```

### 🍴 Pitchfork - Table Access Tool

**Purpose**: Comprehensive table access, filtering, and organization capabilities across multiple documents.

**Key Features**:
- Table cataloging and metadata
- Category-based filtering
- Row-level filtering and search
- Table statistics and analysis
- Document and page context

**Main Methods**:
- `build_catalog()` - Build comprehensive table catalog
- `get_table_catalog()` - Get all available tables
- `get_tables_by_category(category)` - Filter by technical category
- `get_table_rows(table_id, criteria)` - Get rows with optional filtering
- `search_table_values(table_id, search_term)` - Search within table values
- `get_table_statistics(table_id)` - Get comprehensive table statistics

**Usage**:
```python
from pitchfork import Pitchfork
from silo import Silo

silo = Silo()
silo.load_document("doc1", "path/to/data.json")

pitchfork = Pitchfork(silo)
pitchfork.build_catalog()

# Get all compatibility tables
compatibility_tables = pitchfork.get_compatibility_tables()

# Get table rows with filtering
rows = pitchfork.get_table_rows("table_1", {"category": "small"})

# Search within table
matches = pitchfork.search_table_values("table_1", "bread")
```

### 🌾 Scythe - Semantic Search (Stub)

**Purpose**: Future semantic/embedding-based search that understands meaning, not just keywords.

**Status**: Stub implementation - ready for future development

**Planned Features**:
- Embedding-based search
- Semantic similarity matching
- Meaning-aware ranking
- Integration with language models

**Usage** (future):
```python
from scythe import Scythe
from silo import Silo

silo = Silo()
silo.load_document("doc1", "path/to/data.json")

scythe = Scythe(silo)
scythe.build_embeddings()

# Semantic search
results = scythe.semantic_search("What are the nutritional benefits?")
```

### 👨‍🌾 Farmer - Manager and Orchestrator

**Purpose**: Unified interface that orchestrates all farm tools and provides a comprehensive API for working with PB&J data.

**Key Features**:
- Automatic tool initialization
- Unified search interface
- Comprehensive data overview
- Document management
- Statistics and monitoring

**Main Methods**:
- `load_document(doc_id, data_path)` - Load document and initialize tools
- `search(query, search_type, limit)` - Unified search interface
- `get_table_catalog()` - Get all available tables
- `get_data_overview()` - Get comprehensive data overview
- `get_farm_stats()` - Get statistics about all tools

**Usage**:
```python
from farmer import Farmer

farmer = Farmer()
farmer.load_document("doc1", "path/to/data.json")

# Search for content
results = farmer.search("peanut butter", search_type="all", limit=5)

# Get table catalog
tables = farmer.get_table_catalog()

# Get data overview
overview = farmer.get_data_overview()
```

### 🏠 Barn - RAG Agent

**Purpose**: Conversational interface for PB&J data that provides intelligent responses based on retrieved context from the Farmer.

**Key Features**:
- Conversational query interface
- Context-aware response generation
- Integration with Farmer for data access
- Configurable LLM backends
- Structured response formatting
- Source attribution and confidence scoring

**Main Methods**:
- `query(question, search_type)` - Process conversational query
- `set_llm_client(llm_client)` - Set LLM client for response generation
- `set_prompt_template(template)` - Set custom prompt template
- `get_data_overview()` - Get overview of available data
- `get_available_documents()` - Get list of available document IDs

**Usage**:
```python
from barn import Barn

# Initialize Barn with data
barn = Barn("path/to/pb&j_data")

# Set up LLM client (optional)
# barn.set_llm_client(your_llm_client)

# Ask questions conversationally
response = barn.query("What are the main ingredients in peanut butter?")

print(f"Answer: {response.answer}")
print(f"Sources: {len(response.sources)}")
print(f"Confidence: {response.context.confidence_score}")

# Customize prompt template
custom_prompt = """You are a helpful cooking assistant.

Context Information:
{context}

User Question: {question}

Please provide a clear, helpful answer based on the context.

Answer:"""

barn.set_prompt_template(custom_prompt)
```

**Response Structure**:
```python
@dataclass
class RAGResponse:
    answer: str                    # Generated response
    context: QueryContext         # Query context information
    sources: List[Dict[str, Any]] # Source attribution
    metadata: Dict[str, Any]      # Additional metadata

@dataclass
class QueryContext:
    question: str                 # Original question
    retrieved_data: Dict[str, Any] # Retrieved context data
    document_ids: List[str]       # Relevant document IDs
    confidence_score: float       # Confidence in response
    search_method: str           # Search method used
```

## 🔧 Installation and Setup

1. **Requirements**: Python 3.7+
2. **Dependencies**: Standard library only (no external dependencies)
3. **Data Format**: Expects PB&J pipeline `final_output.json` files

## 📊 Data Structure

The system expects PB&J pipeline output with the following structure:

```json
{
  "document_info": {...},
  "document_summary": {
    "combined_keywords": [...]
  },
  "pages": [
    {
      "page_id": "page_1",
      "title": "...",
      "summary": "...",
      "keywords": [...],
      "tables": [...]
    }
  ]
}
```

## 🎯 Use Cases

### RAG Systems
- **Document Retrieval**: Use Sickle for fast keyword-based document retrieval
- **Table Access**: Use Pitchfork for structured data queries
- **Context Building**: Combine search results for context generation

### Data Analysis
- **Table Statistics**: Use Pitchfork for comprehensive table analysis
- **Data Filtering**: Filter tables and rows by various criteria
- **Cross-Document Analysis**: Analyze data across multiple documents

### PDF Integration
- **Page Highlighting**: Use page numbers for PDF annotation
- **Content Mapping**: Map search results to specific PDF pages
- **Document Navigation**: Navigate between documents and pages

## 🔄 Extending the System

### Adding New Tools
1. Create a new tool class that accepts a `Silo` instance
2. Implement the tool's functionality
3. Add the tool to the `Farmer` class
4. Update the `Farmer.is_ready()` method

### Adding New Search Types
1. Extend the `Sickle` class with new search methods
2. Add corresponding methods to the `Farmer` class
3. Update documentation and demos

### Adding New Table Operations
1. Extend the `Pitchfork` class with new table operations
2. Add corresponding methods to the `Farmer` class
3. Update documentation and demos

## 🧪 Testing

Run the comprehensive demo:
```bash
python3 demo_farm.py
```

The demo showcases:
- Document loading and statistics
- Keyword search across different types
- Table access and filtering
- Page-level access
- Advanced queries
- Document management

## 🤝 Contributing

1. Follow the farm theme for naming
2. Maintain separation of concerns
3. Add comprehensive documentation
4. Include demo examples
5. Ensure type safety

## 📝 License

This project is part of the PB&J pipeline ecosystem.

---

*Built with 🌾 farm tools for better data harvesting!* 