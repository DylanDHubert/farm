"""
Barn - The Main RAG Agent for Document Data

The Barn serves as the main interface for conversational queries against processed
document data. It intelligently orchestrates different tools based on the 3-phase
approach: Discovery, Exploration, and Retrieval.

Key Features:
- Intelligent tool selection based on question analysis
- Context-aware response generation
- Integration with new phase-based tools
- Configurable LLM backends
- Structured response formatting
- Function-calling support for tool orchestration
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass

from src.silo import Silo
from src.toolshed.discovery import PageDiscovery, KeywordDiscovery, TableDiscovery
from src.toolshed.exploration import TableExplorer, RelevanceFinder
from src.toolshed.retrieval import TableRetriever, RowRetriever, PageRetriever
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


@dataclass
class FarmStats:
    """Statistics about the farm's data and tools."""
    total_documents: int
    total_pages: int
    total_tables: int
    total_keywords: int
    discovery_tools: int
    exploration_tools: int
    retrieval_tools: int


class Barn:
    """
    The Main RAG Agent for Document Data.
    
    The Barn intelligently orchestrates different tools based on the 3-phase approach:
    - Discovery: Understanding what data is available
    - Exploration: Finding relevant data for a query
    - Retrieval: Getting specific data for analysis
    
    Attributes:
        silo (Silo): The silo instance for data storage
        llm_client: The LLM client for response generation
        prompt_template (str): Template for LLM prompts
        max_context_length (int): Maximum context length for LLM
        confidence_threshold (float): Minimum confidence for responses
        tools (Dict[str, ToolDefinition]): Registry of available tools
        
        # Phase-based tools
        discovery_tools: Discovery phase tools
        exploration_tools: Exploration phase tools
        retrieval_tools: Retrieval phase tools
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
        # Initialize data storage
        self.silo = Silo()
        if data_path:
            # Load the document with a default ID
            self.load_document("default", data_path)
        
        # Initialize LLM components
        self.llm_client = llm_client
        self.max_context_length = max_context_length
        self.confidence_threshold = confidence_threshold
        
        # Default prompt template
        self.prompt_template = prompt_template or self._get_default_prompt()
        
        # Initialize phase-based tools
        self._initialize_tools()
        
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
    
    def _initialize_tools(self):
        """Initialize all phase-based tools."""
        # Discovery tools
        self.page_discovery = PageDiscovery(self.silo)
        self.keyword_discovery = KeywordDiscovery(self.silo)
        self.table_discovery = TableDiscovery(self.silo)
        
        # Exploration tools
        self.table_explorer = TableExplorer(self.silo)
        self.relevance_finder = RelevanceFinder(self.silo)
        
        # Retrieval tools
        self.table_retriever = TableRetriever(self.silo)
        self.row_retriever = RowRetriever(self.silo)
        self.page_retriever = PageRetriever(self.silo)
    
    def _register_tools(self):
        """Register all available tools from the 3 phases."""
        
        # ==================== DISCOVERY TOOLS (Phase 1) ====================
        
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
        
        self.tools["view_keywords"] = ToolDefinition(
            name="view_keywords",
            description="Get overview of all available keywords in the dataset",
            function=self.keyword_discovery.view_keywords,
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        self.tools["view_tables"] = ToolDefinition(
            name="view_tables",
            description="Get overview of all available tables with categories and metadata",
            function=self.table_discovery.view_tables,
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        
        # ==================== EXPLORATION TOOLS (Phase 2) ====================
        
        self.tools["table_summary"] = ToolDefinition(
            name="table_summary",
            description="Get detailed summary of a specific table including metadata, columns, and sample data",
            function=self.table_explorer.table_summary,
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name/title of the table to explore"
                    }
                },
                "required": ["table_name"]
            }
        )
        
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
        
        self.tools["find_relevant_pages"] = ToolDefinition(
            name="find_relevant_pages",
            description="Find pages relevant to the search query using multiple criteria",
            function=self.relevance_finder.find_relevant_pages,
            parameters={
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "Search query to find relevant pages for"
                    }
                },
                "required": ["search_query"]
            }
        )
        
        # ==================== RETRIEVAL TOOLS (Phase 3) ====================
        
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
        
        self.tools["get_row_data"] = ToolDefinition(
            name="get_row_data",
            description="Get rows where the specified column matches the target value",
            function=self.row_retriever.get_row_data,
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name/title of the table to search"
                    },
                    "column": {
                        "type": "string",
                        "description": "Column name to match against"
                    },
                    "target": {
                        "type": "string",
                        "description": "Target value to match (case-insensitive)"
                    }
                },
                "required": ["table_name", "column", "target"]
            }
        )
        
        self.tools["get_page_content"] = ToolDefinition(
            name="get_page_content",
            description="Get page content by title or number",
            function=self.page_retriever.get_page_content,
            parameters={
                "type": "object",
                "properties": {
                    "page_identifier": {
                        "type": ["string", "integer"],
                        "description": "Page title (string) or page number (integer)"
                    }
                },
                "required": ["page_identifier"]
            }
        )
    
    def load_document(self, doc_id: str, data_path: str) -> bool:
        """
        Load a document into the silo.
        
        Args:
            doc_id: Unique identifier for the document
            data_path: Path to the final_output.json file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        return self.silo.load_document(doc_id, data_path)
    
    def load_documents(self, doc_mappings: Dict[str, str]) -> Dict[str, bool]:
        """
        Load multiple documents at once.
        
        Args:
            doc_mappings: {doc_id: data_path} mapping
            
        Returns:
            {doc_id: success_status} mapping
        """
        return self.silo.load_documents(doc_mappings)
    
    def is_ready(self) -> bool:
        """Check if the farm is ready (has data loaded)."""
        return self.silo.is_loaded()
    
    def query(self, question: str) -> RAGResponse:
        """
        Process a natural language query using the 3-phase approach.
        
        Args:
            question: Natural language question to answer
            
        Returns:
            RAGResponse with answer, context, and sources
        """
        if not self.is_ready():
            raise ValueError("Farm not ready. Load documents first.")
        
        # Initialize context
        context_data = {
            "question": question,
            "discovery_data": {},
            "exploration_data": {},
            "retrieval_data": {},
            "tools_used": []
        }
        
        # Phase 1: Discovery - Understand what data is available
        logger.info("Phase 1: Discovery")
        try:
            context_data["discovery_data"] = {
                "pages": self.page_discovery.view_pages(),
                "keywords": self.keyword_discovery.view_keywords(),
                "tables": self.table_discovery.view_tables()
            }
            context_data["tools_used"].append("discovery")
        except Exception as e:
            logger.error(f"Discovery phase failed: {e}")
        
        # Phase 2: Exploration - Find relevant data
        logger.info("Phase 2: Exploration")
        try:
            relevant_tables = self.relevance_finder.find_relevant_tables(question)
            relevant_pages = self.relevance_finder.find_relevant_pages(question)
            
            context_data["exploration_data"] = {
                "relevant_tables": relevant_tables,
                "relevant_pages": relevant_pages
            }
            context_data["tools_used"].append("exploration")
        except Exception as e:
            logger.error(f"Exploration phase failed: {e}")
        
        # Phase 3: Retrieval - Get specific data
        logger.info("Phase 3: Retrieval")
        try:
            retrieval_data = {}
            
            # Get data from most relevant table if available
            if context_data["exploration_data"].get("relevant_tables"):
                top_table = context_data["exploration_data"]["relevant_tables"][0]
                table_name = top_table["table_name"]
                
                # Get table summary
                table_summary = self.table_explorer.table_summary(table_name)
                if table_summary:
                    retrieval_data["table_summary"] = table_summary
                
                # Get full table data
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
        except Exception as e:
            logger.error(f"Retrieval phase failed: {e}")
        
        # Generate response using LLM if available
        if self.llm_client:
            try:
                answer = self._generate_llm_response(question, context_data)
            except Exception as e:
                logger.error(f"LLM response generation failed: {e}")
                answer = self._generate_fallback_response(question, context_data)
        else:
            answer = self._generate_fallback_response(question, context_data)
        
        # Create response
        response = RAGResponse(
            answer=answer,
            context=QueryContext(
                question=question,
                retrieved_data=context_data,
                document_ids=self.silo.get_document_ids(),
                confidence_score=0.8,  # TODO: Calculate actual confidence
                search_method="3-phase",
                tools_used=context_data["tools_used"]
            ),
            sources=self._extract_sources(context_data),
            metadata={
                "phases_completed": len(context_data["tools_used"]),
                "total_pages": len(context_data["discovery_data"].get("pages", [])),
                "total_tables": len(context_data["discovery_data"].get("tables", [])),
                "relevant_tables_found": len(context_data["exploration_data"].get("relevant_tables", [])),
                "relevant_pages_found": len(context_data["exploration_data"].get("relevant_pages", []))
            }
        )
        
        return response
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a specific tool by name.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        return tool.function(**kwargs)
    
    def get_tools_for_function_calling(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for function calling.
        
        Returns:
            List of tool definitions in OpenAI function calling format
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
    
    def get_farm_stats(self) -> FarmStats:
        """Get comprehensive statistics about the farm."""
        if not self.is_ready():
            return FarmStats(0, 0, 0, 0, 0, 0, 0)
        
        discovery_data = {
            "pages": self.page_discovery.view_pages(),
            "keywords": self.keyword_discovery.view_keywords(),
            "tables": self.table_discovery.view_tables()
        }
        
        return FarmStats(
            total_documents=len(self.silo.get_document_ids()),
            total_pages=len(discovery_data["pages"]),
            total_tables=len(discovery_data["tables"]),
            total_keywords=len(discovery_data["keywords"]),
            discovery_tools=3,
            exploration_tools=2,
            retrieval_tools=3
        )
    
    def set_llm_client(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Set up the LLM client for response generation."""
        try:
            import openai
            openai.api_key = api_key
            self.llm_client = openai
            self.llm_model = model
            logger.info(f"LLM client configured with model: {model}")
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
    
    def clear_llm_client(self):
        """Clear the LLM client."""
        self.llm_client = None
        self.llm_model = None
    
    def set_prompt_template(self, template: str):
        """Set a custom prompt template."""
        self.prompt_template = template
    
    def get_available_documents(self) -> List[str]:
        """Get list of available document IDs."""
        return self.silo.get_document_ids()
    
    def _get_default_prompt(self) -> str:
        """Get the default prompt template."""
        return """You are a helpful assistant that answers questions based on document data.

You have access to document data through a 3-phase approach:
1. Discovery: Understanding what data is available
2. Exploration: Finding relevant data for the query
3. Retrieval: Getting specific data for analysis

Use the available data to answer the user's question. If you don't have enough information, say so.

Question: {question}

Available Data:
{context}

Answer the question based on the available data:"""
    
    def _generate_llm_response(self, question: str, context_data: Dict[str, Any]) -> str:
        """Generate response using LLM."""
        if not self.llm_client:
            raise ValueError("LLM client not configured")
        
        # Format context for LLM
        context_str = self._format_context_for_llm(context_data)
        
        # Create prompt
        prompt = self.prompt_template.format(
            question=question,
            context=context_str
        )
        
        # Call LLM
        if not self.llm_model:
            raise ValueError("LLM model not configured")
            
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on document data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_context_length,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        if content is None:
            return "No response generated from LLM"
        return content
    
    def _generate_fallback_response(self, question: str, context_data: Dict[str, Any]) -> str:
        """Generate a fallback response without LLM."""
        context_str = self._format_context_for_llm(context_data)
        
        return f"""Question: {question}

Based on the available data:

{context_str}

Note: This is a fallback response. For better answers, configure an LLM client."""
    
    def _format_context_for_llm(self, context_data: Dict[str, Any]) -> str:
        """Format context data for LLM consumption."""
        lines = []
        
        # Discovery data
        if context_data.get("discovery_data"):
            lines.append("=== DISCOVERY DATA ===")
            discovery = context_data["discovery_data"]
            
            if discovery.get("pages"):
                lines.append(f"Pages available: {len(discovery['pages'])}")
                for page in discovery["pages"][:3]:  # Show first 3
                    lines.append(f"  - Page {page['page_number']}: {page['page_title']}")
                if len(discovery["pages"]) > 3:
                    lines.append(f"  ... and {len(discovery['pages']) - 3} more pages")
            
            if discovery.get("tables"):
                lines.append(f"Tables available: {len(discovery['tables'])}")
                for table in discovery["tables"][:3]:  # Show first 3
                    lines.append(f"  - {table['table_title']} (Category: {table['category']})")
                if len(discovery["tables"]) > 3:
                    lines.append(f"  ... and {len(discovery['tables']) - 3} more tables")
            
            if discovery.get("keywords"):
                lines.append(f"Keywords available: {len(discovery['keywords'])}")
                lines.append(f"  Sample: {', '.join(discovery['keywords'][:10])}")
        
        # Exploration data
        if context_data.get("exploration_data"):
            lines.append("\n=== EXPLORATION DATA ===")
            exploration = context_data["exploration_data"]
            
            if exploration.get("relevant_tables"):
                lines.append(f"Relevant tables found: {len(exploration['relevant_tables'])}")
                for table in exploration["relevant_tables"][:3]:  # Show first 3
                    lines.append(f"  - {table['table_name']} (Score: {table['relevance_score']:.2f}, Relation: {table['relation']})")
            
            if exploration.get("relevant_pages"):
                lines.append(f"Relevant pages found: {len(exploration['relevant_pages'])}")
                for page in exploration["relevant_pages"][:3]:  # Show first 3
                    lines.append(f"  - {page['page_title']} (Score: {page['relevance_score']:.2f}, Relation: {page['relation']})")
        
        # Retrieval data
        if context_data.get("retrieval_data"):
            lines.append("\n=== RETRIEVAL DATA ===")
            retrieval = context_data["retrieval_data"]
            
            if retrieval.get("table_summary"):
                summary = retrieval["table_summary"]
                lines.append(f"Table: {summary['table_title']}")
                lines.append(f"  Category: {summary['category']}")
                lines.append(f"  Dimensions: {summary['row_count']} rows × {summary['column_count']} columns")
                lines.append(f"  Columns: {', '.join([col['name'] for col in summary['columns'][:5]])}")
            
            if retrieval.get("table_data"):
                data = retrieval["table_data"]
                lines.append(f"Table data: {data['row_count']} rows available")
                if data.get("rows"):
                    lines.append("  Sample rows:")
                    for i, row in enumerate(data["rows"][:2]):  # Show first 2 rows
                        lines.append(f"    Row {i+1}: {row}")
            
            if retrieval.get("page_content"):
                content = retrieval["page_content"]
                lines.append(f"Page: {content['page_title']}")
                lines.append(f"  Content length: {len(content['content'])} characters")
                lines.append(f"  Tables on page: {content['table_count']}")
        
        return "\n".join(lines)
    
    def _extract_sources(self, context_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract source information from context data."""
        sources = []
        
        # Add table sources
        if context_data.get("retrieval_data", {}).get("table_summary"):
            table = context_data["retrieval_data"]["table_summary"]
            sources.append({
                "type": "table",
                "title": table["table_title"],
                "page": table["page_number"],
                "category": table["category"]
            })
        
        # Add page sources
        if context_data.get("retrieval_data", {}).get("page_content"):
            page = context_data["retrieval_data"]["page_content"]
            sources.append({
                "type": "page",
                "title": page["page_title"],
                "page_number": page["page_number"]
            })
        
        return sources 