# PB&J RAG System - 3-Phase Architecture Documentation

## Overview

The PB&J RAG (Retrieval-Augmented Generation) system implements a **3-phase approach** for intelligent document data retrieval and analysis. The system is built around a clean separation of concerns with `Barn` as the main RAG agent and `Farmer` as the unified access layer.

## Core Architecture

### 1. System Components

#### A. Barn (Main RAG Agent)
The `Barn` class serves as the intelligent RAG agent that orchestrates the 3-phase approach:
- **Discovery**: Understanding what data is available
- **Exploration**: Finding relevant data for a query  
- **Retrieval**: Getting specific data for analysis

#### B. Farmer (Unified Access Layer)
The `Farmer` class provides a simple, clean interface for external applications:
- Abstracts away the complexity of the 3-phase approach
- Provides easy-to-use methods for common operations
- Recommended entry point for external applications

#### C. Silo (Data Foundation)
The `Silo` class manages data storage and provides the foundation for all data access.

### 2. 3-Phase Approach

The system implements a structured 3-phase approach to data retrieval:

#### Phase 1: Discovery
Understanding what data is available in the system.

**Tools:**
- `view_pages()` - Get overview of all available pages with titles and numbers
- `view_keywords()` - Get overview of all available keywords in the dataset
- `view_tables()` - Get overview of all available tables with categories and metadata

#### Phase 2: Exploration
Finding relevant data for a specific query.

**Tools:**
- `find_relevant_tables(search_query)` - Find tables relevant to the search query using multiple criteria
- `find_relevant_pages(search_query)` - Find pages relevant to the search query using multiple criteria
- `table_summary(table_name)` - Get detailed summary of a specific table including metadata, columns, and sample data

#### Phase 3: Retrieval
Getting specific data for analysis.

**Tools:**
- `get_table_data(table_name, columns)` - Get table data with optional column filtering
- `get_row_data(table_name, column, target)` - Get rows where the specified column matches the target value
- `get_page_content(page_identifier)` - Get page content by title or number

## Tool Registry System

### 1. Tool Definition

Each tool is defined with a standardized structure:

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]  # JSON Schema for parameters
```

### 2. Tool Registration

Tools are automatically registered when the `Barn` is initialized:

```python
def _register_tools(self):
    """Register all available tools from the 3 phases."""
    
    # Discovery tools
    self.tools["view_pages"] = ToolDefinition(
        name="view_pages",
        description="Get overview of all available pages with titles and numbers",
        function=self.page_discovery.view_pages,
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
    
    # Exploration tools
    self.tools["find_relevant_tables"] = ToolDefinition(
        name="find_relevant_tables",
        description="Find tables relevant to the search query using multiple criteria",
        function=self.relevance_finder.find_relevant_tables,
        parameters={
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "Search query to find relevant tables for"
                }
            },
            "required": ["search_query"]
        }
    )
    
    # Retrieval tools
    self.tools["get_table_data"] = ToolDefinition(
        name="get_table_data",
        description="Get table data with optional column filtering",
        function=self.table_retriever.get_table_data,
        parameters={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name/title of the table to retrieve"
                },
                "columns": {
                    "type": ["string", "array"],
                    "description": "'all' or list of column names to include",
                    "default": "all"
                }
            },
            "required": ["table_name"]
        }
    )
```

### 3. Tool Calling

Tools can be called directly using the `call_tool` method:

```python
# Call discovery tools
pages = barn.call_tool("view_pages")
keywords = barn.call_tool("view_keywords")
tables = barn.call_tool("view_tables")

# Call exploration tools
relevant_tables = barn.call_tool("find_relevant_tables", search_query="nutrition")
relevant_pages = barn.call_tool("find_relevant_pages", search_query="peanut butter")

# Call retrieval tools
table_data = barn.call_tool("get_table_data", table_name="Nutrition Information")
page_content = barn.call_tool("get_page_content", page_identifier="Page 1")
```

### 4. Function-Calling Support

The system provides function-calling support for LLM integration:

```python
# Get tools formatted for function-calling APIs
tools_for_llm = barn.get_tools_for_function_calling()

# Example output format:
[
    {
        "type": "function",
        "function": {
            "name": "view_pages",
            "description": "Get overview of all available pages with titles and numbers",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_relevant_tables",
            "description": "Find tables relevant to the search query using multiple criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "Search query to find relevant tables for"
                    }
                },
                "required": ["search_query"]
            }
        }
    }
]
```

## Query Processing Flow

### 1. 3-Phase Processing

When a query is received, the system automatically processes it through all three phases:

```python
def query(self, question: str) -> RAGResponse:
    """Process a natural language query using the 3-phase approach."""
    
    # Initialize context
    context_data = {
        "question": question,
        "discovery_data": {},
        "exploration_data": {},
        "retrieval_data": {},
        "tools_used": []
    }
    
    # Phase 1: Discovery - Understand what data is available
    context_data["discovery_data"] = {
        "pages": self.page_discovery.view_pages(),
        "keywords": self.keyword_discovery.view_keywords(),
        "tables": self.table_discovery.view_tables()
    }
    context_data["tools_used"].append("discovery")
    
    # Phase 2: Exploration - Find relevant data
    relevant_tables = self.relevance_finder.find_relevant_tables(question)
    relevant_pages = self.relevance_finder.find_relevant_pages(question)
    
    context_data["exploration_data"] = {
        "relevant_tables": relevant_tables,
        "relevant_pages": relevant_pages
    }
    context_data["tools_used"].append("exploration")
    
    # Phase 3: Retrieval - Get specific data
    retrieval_data = {}
    
    # Get data from most relevant table if available
    if context_data["exploration_data"].get("relevant_tables"):
        top_table = context_data["exploration_data"]["relevant_tables"][0]
        table_name = top_table["table_name"]
        
        table_summary = self.table_explorer.table_summary(table_name)
        if table_summary:
            retrieval_data["table_summary"] = table_summary
        
        table_data = self.table_retriever.get_table_data(table_name)
        if table_data:
            retrieval_data["table_data"] = table_data
    
    # Get data from most relevant page if available
    if context_data["exploration_data"].get("relevant_pages"):
        top_page = context_data["exploration_data"]["relevant_pages"][0]
        page_title = top_page["page_title"]
        
        page_content = self.page_retriever.get_page_content(page_title)
        if page_content:
            retrieval_data["page_content"] = page_content
    
    context_data["retrieval_data"] = retrieval_data
    context_data["tools_used"].append("retrieval")
    
    # Generate response using LLM if available
    if self.llm_client:
        answer = self._generate_llm_response(question, context_data)
    else:
        answer = self._generate_fallback_response(question, context_data)
    
    return RAGResponse(answer=answer, context=context_data, ...)
```

### 2. Response Structure

The system returns structured responses with comprehensive context:

```python
@dataclass
class RAGResponse:
    answer: str
    context: QueryContext
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class QueryContext:
    question: str
    retrieved_data: Dict[str, Any]
    document_ids: List[str]
    confidence_score: float
    search_method: str
    tools_used: List[str]
```

## Usage Examples

### 1. Basic Usage with Farmer (Recommended)

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

# Get sources
sources = farmer.get_sources("What ingredients are listed?")
print(sources)
```

### 2. Discovery Operations

```python
# Get overview of available data
pages = farmer.get_pages()
keywords = farmer.get_keywords()
tables = farmer.get_tables()

print(f"Available pages: {len(pages)}")
print(f"Available keywords: {len(keywords)}")
print(f"Available tables: {len(tables)}")
```

### 3. Exploration Operations

```python
# Find relevant data
relevant_tables = farmer.find_tables("nutrition")
relevant_pages = farmer.find_pages("peanut butter")

# Get table summary
table_summary = farmer.get_table_summary("Nutrition Information")
print(f"Table has {table_summary['row_count']} rows and {table_summary['column_count']} columns")
```

### 4. Retrieval Operations

```python
# Get table data
table_data = farmer.get_table_data("Nutrition Information")
print(f"Retrieved {table_data['row_count']} rows")

# Get specific rows
rows = farmer.get_rows("Nutrition Information", "Item", "Peanut Butter")
print(f"Found {len(rows['rows'])} matching rows")

# Get page content
page_content = farmer.get_page_content("Page 1")
print(f"Page content: {len(page_content['content'])} characters")
```

### 5. Advanced Usage with Barn

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

# Get function-calling format for LLM integration
tools = barn.get_tools_for_function_calling()
```

## LLM Integration

### 1. Configuration

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

### 2. Custom Prompts

```python
# Set custom prompt template
barn.set_prompt_template("""
You are a helpful assistant that answers questions about document data.

Question: {question}

Available Data:
{context}

Please provide a clear, accurate answer based on the available data.
""")
```

## Error Handling

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

## Performance Considerations

### 1. Caching
- Discovery results are cached during the session
- Tool results are not cached by default to ensure fresh data

### 2. LLM Optimization
- Context is formatted efficiently for LLM consumption
- Fallback responses are available when LLM is not configured
- Configurable context length limits

### 3. Tool Efficiency
- Tools are designed for minimal computational overhead
- Relevance scoring uses efficient string matching algorithms
- Table operations are optimized for structured data access

## Future Enhancements

### 1. Semantic Search
- Integration with embedding-based search for better relevance
- Vector similarity for finding related content

### 2. Advanced Caching
- Persistent caching of discovery and exploration results
- Intelligent cache invalidation based on data changes

### 3. Multi-Document Support
- Enhanced support for multiple document types
- Cross-document relationship mapping

### 4. Streaming Responses
- Real-time response generation for long queries
- Progressive disclosure of information 