# 🌾 Farm-Themed PB&J RAG System

A modular, farm-themed RAG (Retrieval-Augmented Generation) system for intelligent document data retrieval and analysis. Built with a 3-phase approach and clean separation of concerns.

## 🏗️ Architecture Overview

The system implements a **3-phase approach** for intelligent data retrieval:

- **🔍 Discovery**: Understanding what data is available
- **🔎 Exploration**: Finding relevant data for a query  
- **📥 Retrieval**: Getting specific data for analysis

### Core Components

- **🌾 Silo**: Data foundation and storage
- **🏠 Barn**: Main RAG agent with 3-phase orchestration
- **👨‍🌾 Farmer**: Unified access layer for external applications
- **🛠️ Toolshed**: Phase-based tools organized by functionality

## 📁 File Structure

```
├── src/
│   ├── silo.py                    # Data foundation and storage
│   ├── barn.py                    # Main RAG agent (3-phase orchestration)
│   ├── farmer.py                  # Unified access layer
│   ├── toolshed/                  # Phase-based tools
│   │   ├── discovery/             # Phase 1: Discovery tools
│   │   │   ├── page_discovery.py
│   │   │   ├── keyword_discovery.py
│   │   │   └── table_discovery.py
│   │   ├── exploration/           # Phase 2: Exploration tools
│   │   │   ├── table_explorer.py
│   │   │   └── relevance_finder.py
│   │   └── retrieval/             # Phase 3: Retrieval tools
│   │       ├── table_retriever.py
│   │       ├── row_retriever.py
│   │       └── page_retriever.py
│   └── models/                    # Data models
├── devtools/
│   └── streamlit_app.py          # Streamlit demo application
├── data/                         # Sample data
├── docs.md                       # Detailed documentation
├── toolkit.md                    # Tool reference
└── README.md                     # This documentation
```

## 🚀 Quick Start

### Basic Usage (Recommended)

```python
from src.farmer import Farmer

# Initialize with data
farmer = Farmer(data_path="data/final_output.json")

# Ask questions
response = farmer.ask("What are the nutritional values of peanut butter?")
print(response.answer)

# Get just the answer
answer = farmer.get_answer("How many calories are in a serving?")
print(answer)
```

### Advanced Usage

```python
from src.barn import Barn

# Initialize with LLM
barn = Barn(
    data_path="data/final_output.json",
    llm_client=openai_client
)

# Direct tool calling
pages = barn.call_tool("view_pages")
relevant_tables = barn.call_tool("find_relevant_tables", search_query="nutrition")
```

## 📚 Detailed Documentation

### 🌾 Silo - Data Foundation

**Purpose**: Standalone data container that loads and organizes structured data from PB&J pipeline outputs.

**Key Features**:
- Multi-document support
- Unified data access
- Document metadata tracking
- Pure data storage (no search logic)

**Main Methods**:
- `load_document(doc_id, data_path)` - Load single document
- `load_documents(doc_mappings)` - Load multiple documents
- `get_all_pages()` - Get all pages with document context
- `get_all_tables()` - Get all tables with document context
- `get_statistics()` - Get comprehensive data statistics

**Usage**:
```python
from src.silo import Silo

silo = Silo()
silo.load_document("doc1", "path/to/data.json")
pages = silo.get_all_pages()
tables = silo.get_all_tables()
```

### 🏠 Barn - Main RAG Agent

**Purpose**: Intelligent RAG agent that orchestrates the 3-phase approach for document data retrieval and analysis.

**Key Features**:
- 3-phase processing (Discovery, Exploration, Retrieval)
- LLM integration for response generation
- Tool registry and function-calling support
- Structured response formatting
- Context-aware query processing

**Main Methods**:
- `query(question)` - Process natural language queries
- `call_tool(tool_name, **kwargs)` - Call specific tools
- `get_tools_for_function_calling()` - Get tools for LLM integration
- `set_llm_client(api_key, model)` - Configure LLM

**Usage**:
```python
from src.barn import Barn

barn = Barn(data_path="data/final_output.json")

# Process queries
response = barn.query("What are the compatibility issues?")

# Direct tool access
pages = barn.call_tool("view_pages")
tables = barn.call_tool("view_tables")
```

### 👨‍🌾 Farmer - Unified Access Layer

**Purpose**: Simple, clean interface for external applications that abstracts away the complexity of the 3-phase approach.

**Key Features**:
- Easy-to-use methods for common operations
- Automatic 3-phase processing
- LLM configuration
- Comprehensive data access

**Main Methods**:
- `ask(question)` - Ask questions and get comprehensive responses
- `get_answer(question)` - Get just the answer text
- `get_sources(question)` - Get sources used to answer
- `get_pages()` - Get overview of available pages
- `get_tables()` - Get overview of available tables
- `find_tables(search_query)` - Find relevant tables
- `get_table_data(table_name)` - Get table data

**Usage**:
```python
from src.farmer import Farmer

farmer = Farmer(data_path="data/final_output.json")

# Ask questions
response = farmer.ask("What are the nutritional values?")
print(response.answer)

# Discovery operations
pages = farmer.get_pages()
keywords = farmer.get_keywords()
tables = farmer.get_tables()

# Exploration operations
relevant_tables = farmer.find_tables("nutrition")
table_summary = farmer.get_table_summary("Nutrition Information")

# Retrieval operations
table_data = farmer.get_table_data("Nutrition Information")
rows = farmer.get_rows("Nutrition Information", "Item", "Peanut Butter")
```

### 🛠️ Toolshed - Phase-Based Tools

The toolshed contains specialized tools organized by the 3-phase approach:

#### Phase 1: Discovery Tools
- **PageDiscovery**: Overview of available pages
- **KeywordDiscovery**: Overview of available keywords  
- **TableDiscovery**: Overview of available tables

#### Phase 2: Exploration Tools
- **TableExplorer**: Detailed table analysis and summaries
- **RelevanceFinder**: Finding relevant tables and pages for queries

#### Phase 3: Retrieval Tools
- **TableRetriever**: Getting table data with filtering
- **RowRetriever**: Getting specific table rows
- **PageRetriever**: Getting page content

## 🔧 3-Phase Processing

### Phase 1: Discovery
Understanding what data is available in the system.

```python
# Get overview of available data
pages = farmer.get_pages()      # All pages with titles and numbers
keywords = farmer.get_keywords() # All available keywords
tables = farmer.get_tables()    # All tables with categories
```

### Phase 2: Exploration
Finding relevant data for a specific query.

```python
# Find relevant data
relevant_tables = farmer.find_tables("nutrition")
relevant_pages = farmer.find_pages("peanut butter")

# Get detailed summaries
table_summary = farmer.get_table_summary("Nutrition Information")
```

### Phase 3: Retrieval
Getting specific data for analysis.

```python
# Get table data
table_data = farmer.get_table_data("Nutrition Information")
rows = farmer.get_rows("Nutrition Information", "Item", "Peanut Butter")
page_content = farmer.get_page_content("Page 1")
```

## 🤖 LLM Integration

### Configuration

```python
# Configure LLM for better responses
farmer.configure_llm(api_key="your-openai-api-key", model="gpt-3.5-turbo")

# Or configure during initialization
farmer = Farmer(
    data_path="data/final_output.json",
    llm_api_key="your-openai-api-key",
    llm_model="gpt-4"
)
```

### Function-Calling Support

```python
# Get tools for LLM integration
tools = barn.get_tools_for_function_calling()

# Use with OpenAI function calling
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What are the nutritional values?"}],
    tools=tools,
    tool_choice="auto"
)
```

## 📊 Response Structure

The system returns structured responses with comprehensive context:

```python
@dataclass
class RAGResponse:
    answer: str                    # Generated answer
    context: QueryContext          # Query context and metadata
    sources: List[Dict[str, Any]]  # Source information
    metadata: Dict[str, Any]       # Additional metadata

@dataclass
class QueryContext:
    question: str                  # Original question
    retrieved_data: Dict[str, Any] # Retrieved data from all phases
    document_ids: List[str]        # Document IDs used
    confidence_score: float        # Confidence in the answer
    search_method: str             # Method used ("3-phase")
    tools_used: List[str]          # Tools used in processing
```

## 🎯 Usage Examples

### Basic Query Processing

```python
from src.farmer import Farmer

farmer = Farmer(data_path="data/final_output.json")

# Simple question answering
response = farmer.ask("What are the nutritional values of peanut butter?")
print(f"Answer: {response.answer}")
print(f"Sources: {len(response.sources)} sources found")
print(f"Tools used: {response.context.tools_used}")
```

### Data Exploration

```python
# Get system overview
stats = farmer.get_stats()
print(f"Documents: {stats.total_documents}")
print(f"Pages: {stats.total_pages}")
print(f"Tables: {stats.total_tables}")
print(f"Keywords: {stats.total_keywords}")

# Explore available data
pages = farmer.get_pages()
for page in pages[:3]:
    print(f"Page {page['page_number']}: {page['page_title']}")

tables = farmer.get_tables()
for table in tables[:3]:
    print(f"Table: {table['table_title']} (Category: {table['category']})")
```

### Advanced Table Operations

```python
# Find relevant tables
relevant_tables = farmer.find_tables("nutrition")
for table in relevant_tables:
    print(f"Relevant: {table['table_name']} (Score: {table['relevance_score']:.2f})")

# Get table data
table_data = farmer.get_table_data("Nutrition Information")
print(f"Table has {table_data['row_count']} rows and {table_data['column_count']} columns")

# Get specific rows
rows = farmer.get_rows("Nutrition Information", "Item", "Peanut Butter")
for row in rows['rows']:
    print(f"Row: {row}")
```

### LLM-Enhanced Responses

```python
# Configure LLM
farmer.configure_llm(api_key="your-openai-api-key", model="gpt-4")

# Get enhanced responses
response = farmer.ask("Compare the nutritional values of peanut butter and jelly")
print(response.answer)

# Get sources
sources = farmer.get_sources("What are the main ingredients?")
for source in sources:
    print(f"Source: {source['type']} - {source['title']}")
```

## 🚀 Installation and Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file for LLM configuration:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

### Data Format

The system expects PB&J pipeline output in JSON format:

```json
{
  "pages": [...],
  "tables": [...],
  "keywords": [...],
  "metadata": {...}
}
```

## 🔍 Error Handling

The system includes comprehensive error handling:

```python
try:
    response = farmer.ask("What is the nutritional content?")
    print(response.answer)
except ValueError as e:
    print(f"System not ready: {e}")
except Exception as e:
    print(f"Error processing query: {e}")
```

## 📈 Performance Considerations

### Caching
- Discovery results are cached during the session
- Tool results are not cached by default for fresh data

### LLM Optimization
- Context is formatted efficiently for LLM consumption
- Fallback responses available when LLM is not configured
- Configurable context length limits

### Tool Efficiency
- Tools designed for minimal computational overhead
- Relevance scoring uses efficient string matching
- Table operations optimized for structured data

## 🔮 Future Enhancements

### Semantic Search
- Integration with embedding-based search
- Vector similarity for better relevance

### Advanced Caching
- Persistent caching of discovery and exploration results
- Intelligent cache invalidation

### Multi-Document Support
- Enhanced support for multiple document types
- Cross-document relationship mapping

### Streaming Responses
- Real-time response generation
- Progressive disclosure of information

## 📖 Additional Documentation

- **[docs.md](docs.md)** - Detailed technical documentation
- **[toolkit.md](toolkit.md)** - Complete tool reference
- **[devtools/streamlit_app.py](devtools/streamlit_app.py)** - Interactive demo application

## 🤝 Contributing

The system is designed for extensibility. Key areas for contribution:

1. **New Tools**: Add tools to the appropriate phase in the toolshed
2. **LLM Integration**: Enhance LLM response generation
3. **Performance**: Optimize tool efficiency and caching
4. **Documentation**: Improve examples and guides

## 📄 License

This project is part of the PB&J pipeline ecosystem for intelligent document processing and analysis. 