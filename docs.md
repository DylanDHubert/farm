# PB&J RAG System - Tool-Based Architecture Documentation

## Overview

The PB&J RAG (Retrieval-Augmented Generation) system is built around a **tool-based architecture** that enables intelligent orchestration of different data access methods. Instead of a monolithic approach, the system exposes granular tools that can be called individually or in combination to answer user queries.

## Core Architecture

### 1. Tool Registry System

The `Barn` class serves as the central tool registry, exposing all available data access methods as callable tools. Each tool is defined with:

- **Name**: Unique identifier for the tool
- **Description**: Human-readable description of what the tool does
- **Function**: The actual callable function
- **Parameters**: JSON Schema defining the tool's parameters

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]  # JSON Schema for parameters
```

### 2. Tool Categories

The system organizes tools into three main categories:

#### A. Pitchfork Tools (Table Operations)
Tools for accessing and manipulating structured table data:

- `get_table_catalog()` - List all available tables with metadata
- `get_table_by_id(table_id, doc_id)` - Get complete table data
- `get_table_info(table_id)` - Get table metadata
- `get_tables_by_category(category)` - Filter tables by technical category
- `get_tables_by_keyword(keyword)` - Find tables by keyword in title/description
- `get_table_rows(table_id, criteria, doc_id)` - Get filtered table rows
- `search_table_values(table_id, search_term, doc_id)` - Search within table data
- `get_compatibility_tables()` - Get all compatibility-related tables
- `get_measurement_tables()` - Get all measurement-related tables

#### B. Sickle Tools (Content Search)
Tools for keyword-based content search across pages:

- `search_content(query, search_type, limit)` - Search across all content
- `search_by_keywords(keywords, search_type, limit)` - Search with specific keywords
- `get_page_by_number(page_number, doc_id)` - Get specific page by number

#### C. Utility Tools
General-purpose tools for system information:

- `get_available_keywords()` - List all indexed keywords
- `get_data_overview()` - Get system overview statistics

## How Tools Work

### 1. Tool Registration

Tools are automatically registered when the `Barn` is initialized:

```python
def _register_tools(self):
    """Register all available tools from Pitchfork and Sickle."""
    
    # Register Pitchfork tools
    self.tools["get_table_catalog"] = ToolDefinition(
        name="get_table_catalog",
        description="Get a list of all available tables with their metadata",
        function=self.farmer.get_table_catalog,
        parameters={"type": "object", "properties": {}, "required": []}
    )
    
    # Register Sickle tools
    self.tools["search_content"] = ToolDefinition(
        name="search_content",
        description="Search for content across all pages using keywords",
        function=self.farmer.search,
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "search_type": {"type": "string", "enum": ["all", "pages", "tables", "titles"]},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    )
```

### 2. Tool Calling

Tools can be called directly using the `call_tool` method:

```python
# Call a specific tool
table_catalog = barn.call_tool("get_table_catalog")
search_results = barn.call_tool("search_content", query="peanut butter", limit=5)
```

### 3. Function-Calling Support

The system provides function-calling support for LLM integration:

```python
# Get tools formatted for function-calling APIs
tools_for_llm = barn.get_tools_for_function_calling()

# Example output format:
[
    {
        "type": "function",
        "function": {
            "name": "get_table_catalog",
            "description": "Get a list of all available tables with their metadata",
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
            "name": "search_content",
            "description": "Search for content across all pages using keywords",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "search_type": {"type": "string", "enum": ["all", "pages", "tables", "titles"]},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        }
    }
]
```

## Query Processing Flow

### 1. Question Analysis

When a query is received, the system analyzes it to determine which tools to use:

```python
def _analyze_question_and_choose_tools(self, question: str) -> List[str]:
    question_lower = question.lower()
    tools_to_use = []
    
    # Check for table-related keywords
    table_keywords = ["table", "data", "chart", "figure", "compatibility", "measurement", "nutrition"]
    if any(keyword in question_lower for keyword in table_keywords):
        tools_to_use.extend([
            "get_table_catalog",
            "get_tables_by_keyword", 
            "get_table_rows",
            "search_table_values"
        ])
    
    # Check for content search keywords
    content_keywords = ["page", "text", "content", "information", "about", "describe"]
    if any(keyword in question_lower for keyword in content_keywords):
        tools_to_use.extend([
            "search_content",
            "search_by_keywords",
            "get_page_by_number"
        ])
    
    return list(set(tools_to_use))  # Remove duplicates
```

### 2. Context Retrieval

The system uses the chosen tools to retrieve relevant context:

```python
def _retrieve_context_with_tools(self, question: str, tools_to_use: List[str]) -> Dict[str, Any]:
    context_data = {
        "question": question,
        "tools_used": tools_to_use,
        "results": {},
        "document_ids": [],
        "confidence": 0.0
    }
    
    # Use each tool to gather information
    for tool_name in tools_to_use:
        try:
            if tool_name == "search_content":
                results = self.call_tool(tool_name, query=question, limit=5)
                context_data["results"][tool_name] = results
            elif tool_name == "get_table_catalog":
                results = self.call_tool(tool_name)
                context_data["results"][tool_name] = results
            # ... handle other tools
        except Exception as e:
            context_data["results"][tool_name] = {"error": str(e)}
    
    return context_data
```

### 3. Response Generation

The system generates responses using either an LLM or fallback logic:

```python
def query(self, question: str, search_type: str = "auto") -> RAGResponse:
    # Step 1: Analyze question and choose tools
    tools_to_use = self._analyze_question_and_choose_tools(question)
    
    # Step 2: Retrieve context using tools
    context_data = self._retrieve_context_with_tools(question, tools_to_use)
    
    # Step 3: Generate response
    if self.llm_client:
        answer = self._generate_llm_response(question, context_data)
    else:
        answer = self._generate_fallback_response(question, context_data)
    
    # Step 4: Return structured response
    return RAGResponse(
        answer=answer,
        context=QueryContext(...),
        sources=self._extract_sources(context_data),
        metadata={...}
    )
```

## Function-Calling Integration

### 1. LLM Tool Calling Pattern

The system supports the modern function-calling pattern where LLMs can:

1. **Analyze the question** and determine which tools to call
2. **Call specific tools** with appropriate parameters
3. **Receive results** and continue reasoning
4. **Call additional tools** if needed
5. **Generate final response** based on all gathered information

### 2. Example Function-Calling Flow

```python
# 1. LLM receives question: "What are the compatibility issues with peanut butter?"

# 2. LLM decides to call tools:
#    - get_compatibility_tables() to find relevant tables
#    - search_content("peanut butter compatibility") for general info

# 3. LLM calls first tool:
tool_call_1 = {
    "name": "get_compatibility_tables",
    "arguments": {}
}

# 4. System returns table information

# 5. LLM calls second tool:
tool_call_2 = {
    "name": "search_content", 
    "arguments": {
        "query": "peanut butter compatibility",
        "limit": 5
    }
}

# 6. System returns search results

# 7. LLM generates final response using all gathered information
```

## Benefits of Tool-Based Architecture

### 1. **Scalability**
- Only retrieve data that's actually needed
- Avoid loading entire datasets into memory
- Efficient for large document collections

### 2. **Extensibility**
- Easy to add new tools without changing core logic
- Support for different data sources and formats
- Modular design allows independent tool development

### 3. **Intelligence**
- LLM can choose the most appropriate tools
- Dynamic tool selection based on question analysis
- Multi-step reasoning with tool chaining

### 4. **Human-like Workflows**
- Mimics how humans search for information
- Start broad, then narrow down
- Use different strategies for different question types

### 5. **Debugging and Transparency**
- Clear visibility into which tools were used
- Easy to trace information sources
- Structured response format with metadata

## Usage Examples

### Basic Tool Usage

```python
from src.barn import Barn

# Initialize Barn with data
barn = Barn(data_path="data/pb&j_20250626_173624/final_output.json")

# Call individual tools
tables = barn.call_tool("get_table_catalog")
search_results = barn.call_tool("search_content", query="peanut butter", limit=3)

# Get function-calling format for LLM
tools_for_llm = barn.get_tools_for_function_calling()
```

### Query Processing

```python
# Process a natural language query
response = barn.query("What are the compatibility issues with peanut butter?")

print(f"Answer: {response.answer}")
print(f"Tools used: {response.context.tools_used}")
print(f"Confidence: {response.context.confidence_score}")
print(f"Sources: {len(response.sources)} sources found")
```

### LLM Integration

```python
import openai

# Set up OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Get tools for function calling
tools = barn.get_tools_for_function_calling()

# Use with OpenAI function calling
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What are the compatibility issues with peanut butter?"}],
    tools=tools,
    tool_choice="auto"
)
```

## Future Enhancements

### 1. **Scythe Integration**
- Add semantic search capabilities
- Embedding-based similarity search
- Hybrid keyword + semantic search

### 2. **Advanced Tool Orchestration**
- Tool chaining and pipelining
- Conditional tool execution
- Result caching and optimization

### 3. **Enhanced Parameter Extraction**
- NLP-based parameter extraction from questions
- Automatic parameter validation
- Smart defaults and suggestions

### 4. **Tool Performance Monitoring**
- Tool usage analytics
- Performance metrics
- Automatic tool optimization

This tool-based architecture provides a flexible, scalable, and intelligent foundation for RAG systems that can adapt to different types of queries and data sources. 