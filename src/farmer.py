"""
Farmer - Unified Access Layer for PB&J RAG System

The Farmer provides a simple, unified interface to the Barn (main RAG agent).
It serves as a clean wrapper that abstracts away the complexity of the 3-phase
approach and provides easy-to-use methods for common operations.

This is the recommended entry point for external applications.
"""

from typing import Dict, List, Optional, Any, Union
from src.barn import Barn, RAGResponse, FarmStats


class Farmer:
    """
    Unified access layer for the PB&J RAG system.
    
    The Farmer provides a simple interface to the Barn's capabilities,
    making it easy to use the RAG system without understanding the
    internal 3-phase architecture.
    
    This is the main entry point for external applications.
    """
    
    def __init__(self, 
                 data_path: Optional[str] = None,
                 llm_api_key: Optional[str] = None,
                 llm_model: str = "gpt-3.5-turbo"):
        """
        Initialize the Farmer with data and optional LLM configuration.
        
        Args:
            data_path: Path to document data file
            llm_api_key: OpenAI API key for LLM responses
            llm_model: LLM model to use (default: gpt-3.5-turbo)
        """
        self.barn = Barn(data_path=data_path)
        
        # Configure LLM if API key provided
        if llm_api_key:
            self.barn.set_llm_client(llm_api_key, llm_model)
    
    def load_document(self, doc_id: str, data_path: str) -> bool:
        """
        Load a document into the system.
        
        Args:
            doc_id: Unique identifier for the document
            data_path: Path to the final_output.json file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        return self.barn.load_document(doc_id, data_path)
    
    def load_documents(self, doc_mappings: Dict[str, str]) -> Dict[str, bool]:
        """
        Load multiple documents at once.
        
        Args:
            doc_mappings: {doc_id: data_path} mapping
            
        Returns:
            {doc_id: success_status} mapping
        """
        return self.barn.load_documents(doc_mappings)
    
    def ask(self, question: str) -> RAGResponse:
        """
        Ask a question and get a comprehensive response.
        
        This is the main method for querying the RAG system.
        It automatically handles the 3-phase approach (Discovery, Exploration, Retrieval)
        and returns a structured response with answer, context, and sources.
        
        Args:
            question: Natural language question to answer
            
        Returns:
            RAGResponse with answer, context, and sources
        """
        return self.barn.query(question)
    
    def get_answer(self, question: str) -> str:
        """
        Get just the answer text for a question.
        
        Args:
            question: Natural language question to answer
            
        Returns:
            Answer text as string
        """
        response = self.barn.query(question)
        return response.answer
    
    def get_sources(self, question: str) -> List[Dict[str, Any]]:
        """
        Get sources used to answer a question.
        
        Args:
            question: Natural language question to answer
            
        Returns:
            List of source information
        """
        response = self.barn.query(question)
        return response.sources
    
    # ==================== DISCOVERY METHODS ====================
    
    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Get overview of all available pages.
        
        Returns:
            List of pages with number, title, and doc_id
        """
        return self.barn.call_tool("view_pages")
    
    def get_keywords(self) -> List[str]:
        """
        Get all available keywords.
        
        Returns:
            List of unique keywords
        """
        return self.barn.call_tool("view_keywords")
    
    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Get overview of all available tables.
        
        Returns:
            List of tables with title, category, and metadata
        """
        return self.barn.call_tool("view_tables")
    
    # ==================== EXPLORATION METHODS ====================
    
    def find_tables(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Find tables relevant to a search query.
        
        Args:
            search_query: Query to find relevant tables for
            
        Returns:
            List of relevant tables with relevance scores
        """
        return self.barn.call_tool("find_relevant_tables", search_query=search_query)
    
    def find_pages(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Find pages relevant to a search query.
        
        Args:
            search_query: Query to find relevant pages for
            
        Returns:
            List of relevant pages with relevance scores
        """
        return self.barn.call_tool("find_relevant_pages", search_query=search_query)
    
    def get_table_summary(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed summary of a specific table.
        
        Args:
            table_name: Name/title of the table
            
        Returns:
            Table summary with metadata, columns, and sample data
        """
        return self.barn.call_tool("table_summary", table_name=table_name)
    
    # ==================== RETRIEVAL METHODS ====================
    
    def get_table_data(self, table_name: str, columns: Union[str, List[str]] = "all") -> Optional[Dict[str, Any]]:
        """
        Get table data with optional column filtering.
        
        Args:
            table_name: Name/title of the table
            columns: "all" or list of column names to include
            
        Returns:
            Table data with rows, columns, and metadata
        """
        return self.barn.call_tool("get_table_data", table_name=table_name, columns=columns)
    
    def get_rows(self, table_name: str, column: str, target: str) -> Optional[Dict[str, Any]]:
        """
        Get rows where a column matches a target value.
        
        Args:
            table_name: Name/title of the table
            column: Column name to match against
            target: Target value to match
            
        Returns:
            Matching rows with metadata
        """
        return self.barn.call_tool("get_row_data", table_name=table_name, column=column, target=target)
    
    def get_page_content(self, page_identifier: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get page content by title or number.
        
        Args:
            page_identifier: Page title (str) or page number (int)
            
        Returns:
            Page content with text, tables, and metadata
        """
        return self.barn.call_tool("get_page_content", page_identifier=page_identifier)
    
    # ==================== UTILITY METHODS ====================
    
    def is_ready(self) -> bool:
        """Check if the system is ready (has data loaded)."""
        return self.barn.is_ready()
    
    def get_stats(self) -> FarmStats:
        """Get comprehensive statistics about the system."""
        return self.barn.get_farm_stats()
    
    def get_documents(self) -> List[str]:
        """Get list of loaded document IDs."""
        return self.barn.get_available_documents()
    
    def configure_llm(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Configure LLM for better responses.
        
        Args:
            api_key: OpenAI API key
            model: LLM model to use
        """
        self.barn.set_llm_client(api_key, model)
    
    def clear_llm(self):
        """Remove LLM configuration."""
        self.barn.clear_llm_client()
    
    def get_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.barn.tools.keys())
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a specific tool by name.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool result
        """
        return self.barn.call_tool(tool_name, **kwargs) 