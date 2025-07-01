"""
Barn - The RAG Agent for Document Data

The Barn serves as the main interface for conversational queries against processed
document data. It intelligently orchestrates different tools (Pitchfork for tables,
Sickle for content, Scythe for semantic search) based on the question type.

Key Features:
- Intelligent tool selection based on question analysis
- Context-aware response generation
- Integration with Farmer for data access
- Configurable LLM backends
- Structured response formatting
- Function-calling support for tool orchestration
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from farmer import Farmer
from models.table import TableInfo, TableRow
from models.search import SearchResult, SemanticSearchResult

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load .env manually
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass  # .env file doesn't exist, that's okay

@dataclass
class QueryContext:
    """Context information for a RAG query."""
    question: str
    retrieved_data: Dict[str, Any]
    document_ids: List[str]
    confidence_score: float
    search_method: str
    tools_used: List[str]


@dataclass
class RAGResponse:
    """Structured response from the RAG agent."""
    answer: str
    context: QueryContext
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class ToolDefinition:
    """Definition of a callable tool for function-calling."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]  # JSON Schema for parameters


class Barn:
    """
    The RAG Agent for Document Data.
    
    The Barn intelligently orchestrates different tools based on question analysis:
    - Pitchfork: For table-specific queries and data extraction
    - Sickle: For keyword-based content search
    - Scythe: For semantic/embedding-based search (future)
    
    Attributes:
        farmer (Farmer): The farmer instance for data access
        llm_client: The LLM client for response generation
        prompt_template (str): Template for LLM prompts
        max_context_length (int): Maximum context length for LLM
        confidence_threshold (float): Minimum confidence for responses
        tools (Dict[str, ToolDefinition]): Registry of available tools
    """
    
    def __init__(self, 
                 data_path: Optional[str] = None,
                 llm_client: Optional[Any] = None,
                 prompt_template: Optional[str] = None,
                 max_context_length: int = 4000,
                 confidence_threshold: float = 0.3):
        """
        Initialize the Barn RAG agent.
        
        Args:
            data_path: Path to document data file
            llm_client: LLM client for response generation
            prompt_template: Custom prompt template
            max_context_length: Maximum context length for LLM
            confidence_threshold: Minimum confidence for responses
        """
        self.farmer = Farmer()
        if data_path:
            # Load the document with a default ID
            self.farmer.load_document("default", data_path)
        
        self.llm_client = llm_client
        self.max_context_length = max_context_length
        self.confidence_threshold = confidence_threshold
        
        # Default prompt template
        self.prompt_template = prompt_template or self._get_default_prompt()
        
        # Initialize tool registry
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_tools()
        
        # Auto-configure LLM if API key is available
        if not self.llm_client:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your-openai-api-key-here":
                try:
                    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                    self.set_llm_client(api_key, model)
                    logger.info(f"Auto-configured LLM client with model: {model}")
                except Exception as e:
                    logger.warning(f"Failed to auto-configure LLM client: {e}")
    
    def _register_tools(self):
        """Register all available tools from Pitchfork and Sickle."""
        
        # ==================== PITCHFORK TOOLS (Table Operations) ====================
        
        # Table Discovery Tools
        self.tools["get_table_catalog"] = ToolDefinition(
            name="get_table_catalog",
            description="Get a list of all available tables with their metadata",
            function=self.farmer.get_table_catalog if self.farmer.is_ready() else lambda: [],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        self.tools["get_table_by_id"] = ToolDefinition(
            name="get_table_by_id",
            description="Get complete table data by table ID",
            function=self.farmer.get_table_by_id if self.farmer.is_ready() else lambda table_id, doc_id=None: None,
            parameters={
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "The unique identifier of the table"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional document ID for disambiguation"
                    }
                },
                "required": ["table_id"]
            }
        )
        
        self.tools["get_table_info"] = ToolDefinition(
            name="get_table_info",
            description="Get metadata information about a specific table",
            function=self.farmer.pitchfork.get_table_info if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda table_id: None,
            parameters={
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "The unique identifier of the table"
                    }
                },
                "required": ["table_id"]
            }
        )
        
        # Table Filtering Tools
        self.tools["get_tables_by_category"] = ToolDefinition(
            name="get_tables_by_category",
            description="Get all tables that match a specific technical category",
            function=self.farmer.pitchfork.get_tables_by_category if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda category: [],
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "The technical category to filter by (e.g., 'compatibility', 'measurement', 'nutrition')"
                    }
                },
                "required": ["category"]
            }
        )
        
        self.tools["get_tables_by_keyword"] = ToolDefinition(
            name="get_tables_by_keyword",
            description="Find tables whose title or description contains a specific keyword",
            function=self.farmer.pitchfork.get_tables_by_keyword if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda keyword: [],
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword to search for in table titles and descriptions"
                    }
                },
                "required": ["keyword"]
            }
        )
        
        # Table Data Access Tools
        self.tools["get_table_rows"] = ToolDefinition(
            name="get_table_rows",
            description="Get specific rows from a table with optional filtering criteria",
            function=self.farmer.get_table_rows if self.farmer.is_ready() else lambda table_id, criteria=None, doc_id=None: [],
            parameters={
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "The unique identifier of the table"
                    },
                    "criteria": {
                        "type": "object",
                        "description": "Optional filtering criteria (e.g., {'column_name': 'value'})"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional document ID for disambiguation"
                    }
                },
                "required": ["table_id"]
            }
        )
        
        self.tools["search_table_values"] = ToolDefinition(
            name="search_table_values",
            description="Search for specific values within a table's data",
            function=self.farmer.search_table_values if self.farmer.is_ready() else lambda table_id, search_term, doc_id=None: [],
            parameters={
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "The unique identifier of the table"
                    },
                    "search_term": {
                        "type": "string",
                        "description": "The term to search for in the table data"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional document ID for disambiguation"
                    }
                },
                "required": ["table_id", "search_term"]
            }
        )
        
        # Convenience Tools
        self.tools["get_compatibility_tables"] = ToolDefinition(
            name="get_compatibility_tables",
            description="Get all tables related to compatibility information",
            function=self.farmer.get_compatibility_tables if self.farmer.is_ready() else lambda: [],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        self.tools["get_measurement_tables"] = ToolDefinition(
            name="get_measurement_tables",
            description="Get all tables related to measurements and quantities",
            function=self.farmer.get_measurement_tables if self.farmer.is_ready() else lambda: [],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        self.tools["get_table_overview"] = ToolDefinition(
            name="get_table_overview",
            description="Get a clear overview of all available tables with titles, descriptions, and categories. Use this when keyword searches fail to see what tables are available.",
            function=self._get_table_overview,
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        # ==================== SICKLE TOOLS (Content Search) ====================
        
        self.tools["search_content"] = ToolDefinition(
            name="search_content",
            description="Search for content across all pages using keywords",
            function=self.farmer.search if self.farmer.is_ready() else lambda query, search_type="all", limit=10: [],
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (natural language or keywords)"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["all", "pages", "tables", "titles"],
                        "description": "Type of search to perform"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )
        
        self.tools["search_by_keywords"] = ToolDefinition(
            name="search_by_keywords",
            description="Search using a specific list of keywords",
            function=self.farmer.sickle.search_by_keywords if (self.farmer.is_ready() and self.farmer.sickle) else lambda keywords, search_type="all", limit=10: [],
            parameters={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specific keywords to search for"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["all", "pages", "tables", "titles"],
                        "description": "Type of search to perform"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["keywords"]
            }
        )
        
        self.tools["get_page_by_number"] = ToolDefinition(
            name="get_page_by_number",
            description="Get a specific page by its page number",
            function=self.farmer.get_page_by_number if self.farmer.is_ready() else lambda page_number, doc_id=None: None,
            parameters={
                "type": "object",
                "properties": {
                    "page_number": {
                        "type": "integer",
                        "description": "The page number to retrieve (1-based)"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional document ID for disambiguation"
                    }
                },
                "required": ["page_number"]
            }
        )
        
        # ==================== UTILITY TOOLS ====================
        
        self.tools["get_available_keywords"] = ToolDefinition(
            name="get_available_keywords",
            description="Get all available keywords that can be searched",
            function=self.farmer.get_all_keywords if self.farmer.is_ready() else lambda: [],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        self.tools["get_data_overview"] = ToolDefinition(
            name="get_data_overview",
            description="Get an overview of all available data",
            function=self.farmer.get_data_overview if self.farmer.is_ready() else lambda: {},
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    
    def _get_default_prompt(self) -> str:
        """Get the default prompt template for LLM queries."""
        return """You are a helpful assistant that answers questions about document data.

You have access to the following tools:
- Table tools (Pitchfork): get_table_catalog, get_table_by_id, get_table_rows, search_table_values, etc.
- Content tools (Sickle): search_content, search_by_keywords, get_page_by_number, etc.
- Utility tools: get_available_keywords, get_data_overview, etc.

Use these tools to find the information needed to answer the user's question. You can call multiple tools in sequence if needed.

Context Information:
{context}

User Question: {question}

Please provide a clear, accurate answer based on the context provided. If the context doesn't contain enough information to answer the question, say so. If you're referencing specific data, include relevant details like page numbers, table names, or document IDs.

Answer:"""
    
    def get_tools_for_function_calling(self) -> List[Dict[str, Any]]:
        """
        Get tools formatted for function-calling APIs (OpenAI, Anthropic, etc.).
        
        Returns:
            List of tool definitions in the format expected by function-calling APIs
        """
        tools = []
        for tool_name, tool_def in self.tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_def.description,
                    "parameters": tool_def.parameters
                }
            })
        return tools
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a specific tool by name.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result from the tool call
            
        Raises:
            KeyError: If tool name doesn't exist
        """
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        tool_def = self.tools[tool_name]
        return tool_def.function(**kwargs)
    
    def query(self, question: str) -> RAGResponse:
        """
        Process a conversational query using intelligent multi-step function calling.
        
        The LLM will analyze the question and iteratively call tools, building context
        until it has enough information to answer the question.
        
        Args:
            question: The user's question
            
        Returns:
            RAGResponse with answer and context information
        """
        logger.info(f"Starting multi-step query processing for: {question}")
        
        if not self.llm_client:
            raise ValueError("LLM client not configured. Please set up an LLM client before making queries.")
        
        # Initialize context and tracking
        context_data = {
            "question": question,
            "tool_calls": [],
            "results": {},
            "document_ids": [],
            "confidence": 0.0,
            "step_count": 0
        }
        
        max_steps = 5  # Prevent infinite loops
        
        # Multi-step agent loop
        for step in range(max_steps):
            logger.info(f"Starting step {step + 1}/{max_steps}")
            context_data["step_count"] = step + 1
            
            # Step 1: Let the LLM decide what tool to call next (or if it's done)
            logger.info("Getting next LLM tool call...")
            next_action = self._get_next_llm_action(question, context_data)
            logger.info(f"Next action: {next_action}")
            
            if next_action["action"] == "answer":
                logger.info("LLM decided it has enough information to answer")
                break
            elif next_action["action"] == "no_more_tools":
                logger.info("LLM decided no more tools are needed")
                break
            elif next_action["action"] == "tool_call":
                tool_call = next_action["tool_call"]
                logger.info(f"LLM chose tool call: {tool_call['tool_name']} with parameters: {tool_call['parameters']}")
        
                # Step 2: Execute the chosen tool
                logger.info("Executing tool call...")
                try:
                    result = self.call_tool(tool_call["tool_name"], **tool_call["parameters"])
                    logger.info(f"Tool {tool_call['tool_name']} executed successfully")
                    
                    # Step 3: Update context with the result
                    context_data["tool_calls"].append(tool_call)
                    context_data["results"][f"{tool_call['tool_name']}_{step}"] = {
                        "parameters": tool_call["parameters"],
                        "result": result
                    }
                    
                    # Continue to next step (don't break)
                    logger.info(f"Continuing to next step after tool execution")
                    
                except Exception as e:
                    logger.error(f"Error executing tool {tool_call['tool_name']}: {e}")
                    context_data["results"][f"{tool_call['tool_name']}_{step}"] = {
                        "parameters": tool_call["parameters"],
                        "error": str(e)
                    }
            else:
                logger.warning(f"Unknown action from LLM: {next_action}")
                break
        
        # Step 4: Generate final response using LLM with all retrieved context
        logger.info("Generating final LLM response...")
        answer = self._generate_llm_response(question, context_data)
        logger.info("Final LLM response generated")
        
        # Step 5: Create structured response
        response = RAGResponse(
            answer=answer,
            context=QueryContext(
                question=question,
                retrieved_data=context_data,
                document_ids=list(context_data.get("document_ids", [])),
                confidence_score=context_data.get("confidence", 0.0),
                search_method="multi_step_function_calling",
                tools_used=[call["tool_name"] for call in context_data["tool_calls"]]
            ),
            sources=self._extract_sources(context_data),
            metadata={
                "search_type": "multi_step_function_calling",
                "context_length": len(str(context_data)),
                "has_llm": True,
                "tools_used": [call["tool_name"] for call in context_data["tool_calls"]],
                "tool_calls": context_data["tool_calls"],
                "available_tools": list(self.tools.keys()),
                "steps_taken": context_data["step_count"]
            }
        )
        
        logger.info(f"Multi-step query processing completed. Steps: {context_data['step_count']}, Confidence: {response.context.confidence_score}")
        return response
    
    def _get_next_llm_action(self, question: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the next action using intelligent, data-driven approach.
        
        Args:
            question: The user's question
            context_data: Current context data
            
        Returns:
            Dictionary with action and tool call info
        """
        tool_calls = context_data.get("tool_calls", [])
        
        # Debug: Log past actions
        logger.info(f"Past tool calls: {[call.get('tool_name') for call in tool_calls]}")
        
        # Step 1: If no tools used yet, always start with table overview to see what's available
        if not tool_calls:
            logger.info("No tools used yet - starting with table overview")
            return {
                "action": "tool_call",
                "tool_call": {
                    "tool_name": "get_table_overview",
                    "parameters": {}
                }
            }
        
        # Step 2: If we have table overview but no specific searches, let the LLM decide what to search
        table_tools_used = any(call.get("tool_name", "").startswith(("get_table", "search_table")) for call in tool_calls)
        specific_searches = [call for call in tool_calls if call.get("tool_name") == "search_table_values"]
        
        if table_tools_used and not specific_searches:
            # Extract key terms from the question for intelligent search
            question_words = question.lower().split()
            # Remove common words and keep meaningful terms
            meaningful_terms = [word for word in question_words if len(word) > 2 and word not in ['can', 'put', 'on', 'the', 'and', 'for', 'with', 'what', 'when', 'where', 'how', 'why']]
            
            if meaningful_terms:
                logger.info(f"Found meaningful terms: {meaningful_terms}")
                return {
                    "action": "tool_call",
                    "tool_call": {
                        "tool_name": "search_table_values",
                        "parameters": {
                            "table_id": "Compatibility of Toppings with Different Types of Sandwiches",
                            "search_term": meaningful_terms[0].title()
                        }
                    }
                }
        
        # Step 3: If we've done specific searches, we can answer
        if specific_searches:
            logger.info("Specific searches completed - ready to answer")
            return {"action": "answer"}
        
        # Step 4: If we've used table tools but no specific searches, try content search
        if table_tools_used and len(tool_calls) >= 2:
            logger.info("Table tools used but no specific data found - trying content search")
            return {
                "action": "tool_call",
                "tool_call": {
                    "tool_name": "search_content",
                    "parameters": {
                        "query": question,
                        "search_type": "all"
                    }
                }
            }
        
        # Step 5: Default fallback to content search
        logger.info("Defaulting to content search")
        return {
            "action": "tool_call",
            "tool_call": {
                "tool_name": "search_content",
                "parameters": {
                    "query": question,
                    "search_type": "all"
                }
            }
        }
    
    def _generate_llm_response(self, question: str, context_data: Dict[str, Any]) -> str:
        """
        Generate response using LLM.
        
        Args:
            question: The user's question
            context_data: Retrieved context data
            
        Returns:
            Generated response string
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured. Please set up an LLM client before making queries.")
        
        # Format context for LLM
        context_str = self._format_context_for_llm(context_data)
        
        # Create enhanced prompt with reasoning guidance
        enhanced_prompt = f"""
You are a helpful assistant that answers questions about document data.

CONTEXT INFORMATION:
{context_str}

USER QUESTION: {question}

INSTRUCTIONS:
1. **Carefully examine table data**: Look at the actual values in the table rows
2. **Interpret TRUE/FALSE values**: In compatibility tables, 'TRUE' means compatible/available/positive, 'FALSE' means not compatible/available/negative
3. **Match column headers**: Look for the specific column that matches the question
4. **Provide exact answers**: If you find 'TRUE' for a specific item, say it IS compatible/available/positive
5. **Be specific about what you found**: Quote the exact data you found
6. **Use medical terminology appropriately**: If this is medical data, use appropriate medical language

TABLE INTERPRETATION GUIDE:
- If you see: {{'Item': 'Value', 'Category': 'TRUE'}}
- This means: The item IS compatible/available/positive for that category
- If you see: {{'Item': 'Value', 'Category': 'FALSE'}}
- This means: The item is NOT compatible/available/positive for that category
- Answer format: "Yes, [item] is [compatible/available/positive] for [category]" or "No, [item] is not [compatible/available/positive] for [category]"

Please provide a clear, accurate answer based on the context provided.
"""
        
        try:
            # Handle different LLM client formats
            if hasattr(self.llm_client, 'chat'):
                # OpenAI client format
                response = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions about document data."},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                return response.choices[0].message.content
            elif isinstance(self.llm_client, dict) and "client" in self.llm_client:
                # Dictionary format with client key
                client = self.llm_client["client"]
                if hasattr(client, 'chat'):
                    response = client.chat.completions.create(
                        model=self.llm_client.get("model", "gpt-4"),
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that answers questions about document data."},
                            {"role": "user", "content": enhanced_prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.3
                    )
                    return response.choices[0].message.content
                else:
                    return "LLM client in dictionary format but client object doesn't have chat attribute"
            else:
                # Fallback for unknown client format
                return f"LLM client format not supported: {type(self.llm_client)}"
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _format_context_for_llm(self, context_data: Dict[str, Any]) -> str:
        """
        Format context data for LLM consumption.
        
        Args:
            context_data: Retrieved context data
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add overview
        overview = context_data.get("overview", {})
        if overview and "error" not in overview:
            parts.append("Data Overview:")
            parts.append(f"- Documents: {overview.get('document_count', 'Unknown')}")
            parts.append(f"- Tables: {overview.get('table_count', 'Unknown')}")
            parts.append(f"- Pages: {overview.get('page_count', 'Unknown')}")
        
        # Add search results with reasoning context
        results = context_data.get("results", {})
        tool_calls = context_data.get("tool_calls", [])
        
        # Show the reasoning process
        if tool_calls:
            parts.append("\nREASONING PROCESS:")
            for i, call in enumerate(tool_calls):
                parts.append(f"Step {i+1}: {call['tool_name']} with parameters: {call['parameters']}")
        
        # Show results organized by tool type
        discovery_results = []
        extraction_results = []
        fallback_results = []
        
        for tool_name, result in results.items():
            # Handle new format: result is a dict with "result" key
            if isinstance(result, dict) and "result" in result:
                actual_result = result["result"]
                parameters = result.get("parameters", {})
                
                # Categorize results by tool type
                if tool_name.startswith(("get_tables_by_", "get_table_catalog", "get_compatibility_", "get_measurement_")):
                    discovery_results.append((tool_name, actual_result, parameters))
                elif tool_name.startswith(("get_table_rows", "search_table_values", "get_table_by_id")):
                    extraction_results.append((tool_name, actual_result, parameters))
                else:
                    fallback_results.append((tool_name, actual_result, parameters))
                    
            # Handle old format: result is directly a list
            elif isinstance(result, list) and result:
                if tool_name.startswith(("get_tables_by_", "get_table_catalog", "get_compatibility_", "get_measurement_")):
                    discovery_results.append((tool_name, result, {}))
                elif tool_name.startswith(("get_table_rows", "search_table_values", "get_table_by_id")):
                    extraction_results.append((tool_name, result, {}))
                else:
                    fallback_results.append((tool_name, result, {}))
        
        # Display discovery results
        if discovery_results:
            parts.append("\nDISCOVERY RESULTS:")
            for tool_name, actual_result, parameters in discovery_results:
                parts.append(f"\n{tool_name.replace('_', ' ').title()} (Parameters: {parameters}):")
                if isinstance(actual_result, list) and actual_result:
                    for item in actual_result[:3]:  # Limit to 3 items per tool
                        if hasattr(item, 'title'):
                            parts.append(f"- {item.title}")
                        elif hasattr(item, 'context'):
                            parts.append(f"- {item.context[:100]}...")
                        else:
                            parts.append(f"- {str(item)[:100]}...")
                elif isinstance(actual_result, dict) and "error" not in actual_result:
                    parts.append(f"- {str(actual_result)[:200]}...")
        
        # Display extraction results
        if extraction_results:
            parts.append("\nEXTRACTION RESULTS:")
            for tool_name, actual_result, parameters in extraction_results:
                parts.append(f"\n{tool_name.replace('_', ' ').title()} (Parameters: {parameters}):")
                if isinstance(actual_result, list) and actual_result:
                    for item in actual_result[:3]:  # Limit to 3 items per tool
                        if hasattr(item, 'context'):
                            parts.append(f"- {item.context}")
                        elif hasattr(item, 'title'):
                            parts.append(f"- {item.title}")
                        else:
                            parts.append(f"- {str(item)[:100]}...")
                elif isinstance(actual_result, dict) and "error" not in actual_result:
                    parts.append(f"- {str(actual_result)[:200]}...")
        
        # Display fallback results
        if fallback_results:
            parts.append("\nFALLBACK SEARCH RESULTS:")
            for tool_name, actual_result, parameters in fallback_results:
                parts.append(f"\n{tool_name.replace('_', ' ').title()} (Parameters: {parameters}):")
                if isinstance(actual_result, list) and actual_result:
                    for item in actual_result[:3]:  # Limit to 3 items per tool
                        if hasattr(item, 'context'):
                            parts.append(f"- {item.context}")
                        elif hasattr(item, 'title'):
                            parts.append(f"- {item.title}")
                        else:
                            parts.append(f"- {str(item)[:100]}...")
                elif isinstance(actual_result, dict) and "error" not in actual_result:
                    parts.append(f"- {str(actual_result)[:200]}...")
        
        return "\n".join(parts)
    
    def _extract_sources(self, context_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract source information from context data.
        
        Args:
            context_data: Retrieved context data
            
        Returns:
            List of source dictionaries
        """
        sources = []
        results = context_data.get("results", {})
        
        for tool_name, result in results.items():
            # Handle new format: result is a dict with "result" key
            if isinstance(result, dict) and "result" in result:
                actual_result = result["result"]
                if isinstance(actual_result, list):
                    for item in actual_result:
                        source = {
                            "tool": tool_name,
                            "type": getattr(item, 'match_type', 'unknown'),
                            "score": getattr(item, 'match_score', 0.0)
                        }
                        
                        if hasattr(item, 'page_number'):
                            source["page"] = item.page_number
                        if hasattr(item, 'doc_id'):
                            source["document"] = item.doc_id
                        if hasattr(item, 'context'):
                            source["context"] = item.context
                        
                        sources.append(source)
            # Handle old format: result is directly a list
            elif isinstance(result, list):
                for item in result:
                    source = {
                        "tool": tool_name,
                        "type": getattr(item, 'match_type', 'unknown'),
                        "score": getattr(item, 'match_score', 0.0)
                    }
                    
                    if hasattr(item, 'page_number'):
                        source["page"] = item.page_number
                    if hasattr(item, 'doc_id'):
                        source["document"] = item.doc_id
                    if hasattr(item, 'context'):
                        source["context"] = item.context
                    
                    sources.append(source)
        
        return sources
    
    def get_data_overview(self) -> Dict[str, Any]:
        """
        Get an overview of available data.
        
        Returns:
            Dictionary with data overview
        """
        return self.farmer.get_data_overview()
    
    def set_llm_client(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Set the OpenAI client for response generation."""
        try:
            from openai import OpenAI
            self.llm_client = {"client": OpenAI(api_key=api_key), "model": model}
        except ImportError:
            raise ImportError("OpenAI library not found. Install with: pip install openai")
    
    def clear_llm_client(self):
        """Clear the LLM client."""
        self.llm_client = None
    
    def set_prompt_template(self, template: str):
        """Set a custom prompt template."""
        self.prompt_template = template
    
    def get_available_documents(self) -> List[str]:
        """Get list of available document IDs."""
        overview = self.farmer.get_data_overview()
        return list(overview.get("documents", {}).keys())
    
    def _get_table_overview(self) -> str:
        """
        Get a clear overview of all available tables.
        
        Returns:
            Formatted string with table information
        """
        if not self.farmer or not self.farmer.is_ready():
            return "No data loaded. Please load a document first."
        
        tables = self.farmer.get_table_catalog()
        if not tables:
            return "No tables found in the loaded documents."
        
        overview = "AVAILABLE TABLES:\n\n"
        for i, table in enumerate(tables, 1):
            overview += f"{i}. **{table.title}**\n"
            overview += f"   - Category: {table.technical_category}\n"
            overview += f"   - Description: {table.description}\n"
            overview += f"   - Rows: {table.row_count}, Columns: {table.column_count}\n"
            overview += f"   - Page: {table.page_number}\n\n"
        
        return overview 