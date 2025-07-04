"""
Toolshed - Collection of RAG Tools

The toolshed contains all the specialized tools for the PB&J RAG system,
organized by phase: Discovery, Exploration, and Retrieval.

Each phase contains tools designed for specific data access patterns,
enabling the Barn to intelligently orchestrate them based on user queries.
"""

# Import all tool classes from each phase
from src.toolshed.discovery import PageDiscovery, KeywordDiscovery, TableDiscovery
from src.toolshed.exploration import TableExplorer, RelevanceFinder
from src.toolshed.retrieval import TableRetriever, RowRetriever, PageRetriever

# Import models
from src.models.table import TableInfo, TableRow
from src.models.search import SearchResult, SemanticSearchResult

__all__ = [
    # Discovery tools
    "PageDiscovery",
    "KeywordDiscovery", 
    "TableDiscovery",
    
    # Exploration tools
    "TableExplorer",
    "RelevanceFinder",
    
    # Retrieval tools
    "TableRetriever",
    "RowRetriever",
    "PageRetriever",
    
    # Models
    "TableInfo", 
    "TableRow",
    "SearchResult",
    "SemanticSearchResult",
] 