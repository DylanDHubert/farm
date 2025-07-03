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
from src.farmer import Farmer
from src.models.table import TableInfo, TableRow
from src.models.search import SearchResult, SemanticSearchResult

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
        
        self.tools["get_table_by_name"] = ToolDefinition(
            name="get_table_by_name",
            description="Get complete table data by table title/name. Use this to access specific tables by their readable names.",
            function=self.farmer.pitchfork.get_table_by_title if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda title, doc_id=None: None,
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title/name of the table (e.g., 'Nutrition Information', 'Surgical Protocol')"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Optional document ID for disambiguation"
                    }
                },
                "required": ["title"]
            }
        )
        
        self.tools["get_table_info"] = ToolDefinition(
            name="get_table_info",
            description="Get metadata information about a specific table by title",
            function=self.farmer.pitchfork.get_table_info if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda title: None,
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title/name of the table"
                    }
                },
                "required": ["title"]
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
                        "description": "The technical category to filter by (e.g., 'technical', 'measurement', 'analysis')"
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
            function=self.farmer.pitchfork.get_table_rows if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda title, criteria=None, doc_id=None: [],
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title/name of the table"
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
                "required": ["title"]
            }
        )
        
        self.tools["search_table_values"] = ToolDefinition(
            name="search_table_values",
            description="Search for specific values within a table's data",
            function=self.farmer.pitchfork.search_table_values if (self.farmer.is_ready() and self.farmer.pitchfork) else lambda title, search_term, doc_id=None: [],
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title/name of the table"
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
                "required": ["title", "search_term"]
            }
        )
        
        
        # Removed domain-specific measurement tables tool
        
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
            description="Search for content across all pages using a natural language query string. Use this for general content searches.",
            function=self.farmer.search if self.farmer.is_ready() else lambda query, search_type="all", limit=10: [],
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query as a single string (e.g., 'B.L.T. sandwich' or 'nutritional information')"
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
            description="Search using a specific list of keywords as an array. Use this when you have exact keywords to search for.",
            function=self.farmer.sickle.search_by_keywords if (self.farmer.is_ready() and self.farmer.sickle) else lambda keywords, search_type="all", limit=10: [],
            parameters={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specific keywords as array (e.g., ['B.L.T.', 'sandwich', 'bacon'])"
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
        
        The system automatically starts with table overview and keywords overview,
        then lets the LLM intelligently choose between Pitchfork (semantic search) 
        and Sickle (keyword search) based on the query context.
        
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
        
        # Step 0: Automatically get table overview and keywords overview
        logger.info("Automatically getting table overview and keywords overview...")
        
        # Get table overview
        try:
            table_overview = self._get_table_overview()
            context_data["results"]["table_overview"] = {
                "parameters": {},
                "result": table_overview
            }
            logger.info("Table overview retrieved successfully")
        except Exception as e:
            logger.error(f"Error getting table overview: {e}")
            context_data["results"]["table_overview"] = {
                "parameters": {},
                "error": str(e)
            }
        
        # Get keywords overview
        try:
            keywords_overview = self._get_keywords_overview()
            context_data["results"]["keywords_overview"] = {
                "parameters": {},
                "result": keywords_overview
            }
            logger.info("Keywords overview retrieved successfully")
        except Exception as e:
            logger.error(f"Error getting keywords overview: {e}")
            context_data["results"]["keywords_overview"] = {
                "parameters": {},
                "error": str(e)
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
                
                # DEBUG: Print tool call to terminal
                print(f"🔧 TOOL CALL: {tool_call['tool_name']} | Params: {tool_call['parameters']}")
        
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
        Get the next action using LLM-based intelligent decision making.
        
        Args:
            question: The user's question
            context_data: Current context data
            
        Returns:
            Dictionary with action and tool call info
        """
        tool_calls = context_data.get("tool_calls", [])
        
        # Debug: Log past actions
        logger.info(f"Past tool calls: {[call.get('tool_name') for call in tool_calls]}")
        
        # Prevent infinite loops by checking for repeated tool calls
        if len(tool_calls) >= 2:
            recent_calls = tool_calls[-2:]
            if (recent_calls[0]['tool_name'] == recent_calls[1]['tool_name'] and 
                recent_calls[0]['parameters'] == recent_calls[1]['parameters']):
                logger.warning("Detected repeated tool call - stopping to prevent infinite loop")
                return {"action": "answer"}
        
        # Use LLM to decide next action
        try:
            # Format context for LLM
            context_str = self._format_context_for_llm(context_data)
            
            # Create decision prompt
            decision_prompt = f"""
You are an intelligent agent that decides what tools to use to answer questions about document data.

AVAILABLE TOOLS:
{self._format_tools_for_llm()}

CURRENT CONTEXT:
{context_str}

USER QUESTION: {question}

TOOL SELECTION STRATEGY:
You have access to two main search approaches:

1. **PITCHFORK (Table Operations)**: Use for questions about:
   - Specific data in tables (numbers, values, measurements)
   - Table structure and metadata
   - Technical categories and descriptions
   - Structured data queries
   - Tools: get_table_catalog, get_table_by_id, get_table_info, get_tables_by_category, etc.

2. **SICKLE (Content Search)**: Use for questions about:
   - General content and concepts
   - Natural language queries
   - Keyword-based searches
   - Page-level information
   - Tools: search_content, search_by_keywords, etc.

INSTRUCTIONS:
1. Analyze the question type and choose the appropriate search approach
2. For table-specific questions (data, measurements, categories), use PITCHFORK tools
3. For content/concept questions, use SICKLE tools
4. You MUST use at least one search tool (Pitchfork or Sickle) to retrieve relevant data before answering, unless the answer is trivially obvious from the overviews.
5. Decide what action to take next:
   - "tool_call": Call a specific tool with parameters
   - "answer": Generate final answer (if you have enough information)
   - "no_more_tools": Stop searching (if no more tools would help)

6. If choosing "tool_call", specify:
   - tool_name: The exact name of the tool to call
   - parameters: A JSON object with the tool's parameters

7. IMPORTANT: Do not repeat the same tool call with the same parameters
8. If you've gathered enough information to answer, choose "answer"

RESPONSE FORMAT:
Return a JSON object with:
- "action": "tool_call" | "answer" | "no_more_tools"
- "tool_call": {{"tool_name": "...", "parameters": {{...}}}} (only if action is "tool_call")

What should I do next?
"""
            
            # Get LLM decision
            if hasattr(self.llm_client, 'chat'):
                # OpenAI client format
                response = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an intelligent agent that decides what tools to use. Respond with valid JSON only."},
                        {"role": "user", "content": decision_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
                decision_text = response.choices[0].message.content
            elif isinstance(self.llm_client, dict) and "client" in self.llm_client:
                # Dictionary format with client key
                client = self.llm_client["client"]
                if hasattr(client, 'chat'):
                    response = client.chat.completions.create(
                        model=self.llm_client.get("model", "gpt-4"),
                        messages=[
                            {"role": "system", "content": "You are an intelligent agent that decides what tools to use. Respond with valid JSON only."},
                            {"role": "user", "content": decision_prompt}
                        ],
                        max_tokens=500,
                        temperature=0.1
                    )
                    decision_text = response.choices[0].message.content
                else:
                    raise ValueError("LLM client format not supported")
            else:
                raise ValueError("LLM client format not supported")
            
            # Parse LLM response
            import json
            try:
                decision = json.loads(decision_text.strip())
                logger.info(f"LLM decision: {decision}")
                return decision
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {decision_text}")
                # Fallback to simple logic
                return self._fallback_action_logic(question, context_data)
                
        except Exception as e:
            logger.error(f"Error getting LLM action: {e}")
            # Fallback to simple logic
            return self._fallback_action_logic(question, context_data)
    
    def _fallback_action_logic(self, question: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback logic when LLM decision fails."""
        tool_calls = context_data.get("tool_calls", [])
        
        # If no tools used yet, start with table overview
        if not tool_calls:
            return {
                "action": "tool_call",
                "tool_call": {
                    "tool_name": "get_table_overview",
                    "parameters": {}
                }
            }
        
        # If we have some data, try to answer
        if len(tool_calls) >= 1:
            return {"action": "answer"}
        
        # Default to content search
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
    
    def _format_tools_for_llm(self) -> str:
        """Format available tools for LLM consumption."""
        tools_info = []
        for tool_name, tool_def in self.tools.items():
            tools_info.append(f"- {tool_name}: {tool_def.description}")
        return "\n".join(tools_info)
    
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
2. **Interpret TRUE/FALSE values**: In data tables, 'TRUE' means available/positive/yes, 'FALSE' means not available/negative/no
3. **Match column headers**: Look for the specific column that matches the question
4. **Provide exact answers**: If you find 'TRUE' for a specific item, say it IS available/positive/yes
5. **Be specific about what you found**: Quote the exact data you found
6. **Use appropriate terminology**: Use language that matches the document's domain

TABLE INTERPRETATION GUIDE:
- If you see: {{'Item': 'Value', 'Category': 'TRUE'}}
- This means: The item IS available/positive/yes for that category
- If you see: {{'Item': 'Value', 'Category': 'FALSE'}}
- This means: The item is NOT available/positive/yes for that category
- Answer format: "Yes, [item] is [available/positive/yes] for [category]" or "No, [item] is not [available/positive/yes] for [category]"

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
                if tool_name.startswith(("get_tables_by_", "get_table_catalog", "get_measurement_")):
                    discovery_results.append((tool_name, actual_result, parameters))
                elif tool_name.startswith(("get_table_rows", "search_table_values", "get_table_by_id")):
                    extraction_results.append((tool_name, actual_result, parameters))
                else:
                    fallback_results.append((tool_name, actual_result, parameters))
                    
            # Handle old format: result is directly a list
            elif isinstance(result, list) and result:
                if tool_name.startswith(("get_tables_by_", "get_table_catalog", "get_measurement_")):
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
    
    def _get_keywords_overview(self) -> str:
        """
        Get a plain list of all available keywords for content search.
        
        Returns:
            String with a simple list of keywords
        """
        if not self.farmer or not self.farmer.is_ready():
            return "No data loaded. Please load a document first."
        
        if not self.farmer.sickle:
            return "No keyword search tool available."
        
        try:
            keywords = self.farmer.sickle.get_available_keywords()
            if not keywords:
                return "No keywords found in the loaded documents."
            
            overview = "AVAILABLE KEYWORDS FOR CONTENT SEARCH:\n"
            overview += ", ".join(keywords)
            return overview
        except Exception as e:
            logger.error(f"Error getting keywords overview: {e}")
            return f"Error retrieving keywords: {str(e)}"
    
    def _find_best_table_for_search(self, table_overview: str, search_term: str) -> Optional[str]:
        """
        Find the best table to search in based on the table overview and search term.
        
        Args:
            table_overview: String containing the table overview
            search_term: Term to search for
            
        Returns:
            Best table title to search in, or None if no good match
        """
        if not table_overview:
            return None
        
        # Extract table titles from the overview
        lines = table_overview.split('\n')
        table_titles = []
        
        for line in lines:
            if line.strip().startswith('**') and line.strip().endswith('**'):
                # Extract title from markdown format: **Title**
                title = line.strip()[2:-2]  # Remove **
                table_titles.append(title)
        
        # Score each table based on relevance to search term
        best_table = None
        best_score = 0
        
        for title in table_titles:
            title_lower = title.lower()
            search_lower = search_term.lower()
            
            # Simple scoring: exact match = 10, contains = 5, word match = 3
            score = 0
            if search_lower in title_lower:
                score += 5
            if search_lower == title_lower:
                score += 10
            
            # Check for word matches
            search_words = search_lower.split()
            title_words = title_lower.split()
            for word in search_words:
                if word in title_words:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_table = title
        
        logger.info(f"Search term '{search_term}' -> best table: '{best_table}' (score: {best_score})")
        return best_table 