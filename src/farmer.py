"""
Farmer - Manager for PB&J Data Tools

The farmer orchestrates all the farm tools (Silo, Sickle, Pitchfork, Scythe)
and provides a unified interface for working with PB&J pipeline data.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from src.silo import Silo
from src.toolshed.pitchfork import Pitchfork
from src.toolshed.sickle import Sickle
from src.toolshed.scythe import Scythe
from models.table import TableInfo, TableRow
from models.search import SearchResult, SemanticSearchResult


@dataclass
class FarmStats:
    """Statistics about the farm's data and tools."""
    silo_stats: Dict[str, Any]
    sickle_stats: Dict[str, Any]
    pitchfork_stats: Dict[str, Any]
    total_documents: int
    total_pages: int
    total_tables: int
    total_keywords: int


class Farmer:
    """
    Manager class that orchestrates all farm tools.
    
    Provides a unified interface for working with PB&J pipeline data,
    coordinating the Silo (data storage), Sickle (keyword search),
    Pitchfork (table access), and future Scythe (semantic search).
    """
    
    def __init__(self):
        """Initialize the farmer with all farm tools."""
        self.silo = Silo()
        self.sickle = None  # Will be initialized when silo has data
        self.pitchfork = None  # Will be initialized when silo has data
        self.scythe = None  # Future semantic search tool
    
    def load_document(self, doc_id: str, data_path: str) -> bool:
        """
        Load a document into the silo and initialize tools.
        
        Args:
            doc_id: Unique identifier for the document
            data_path: Path to the final_output.json file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        success = self.silo.load_document(doc_id, data_path)
        
        if success:
            # Initialize tools if this is the first document
            if not self.sickle:
                self.sickle = Sickle(self.silo)
                self.sickle.build_index()
            
            if not self.pitchfork:
                self.pitchfork = Pitchfork(self.silo)
                self.pitchfork.build_catalog()
            
            # Rebuild indexes if tools already exist
            elif self.sickle:
                self.sickle.build_index()
            
            if self.pitchfork:
                self.pitchfork.build_catalog()
        
        return success
    
    def load_documents(self, doc_mappings: Dict[str, str]) -> Dict[str, bool]:
        """
        Load multiple documents at once.
        
        Args:
            doc_mappings: {doc_id: data_path} mapping
            
        Returns:
            {doc_id: success_status} mapping
        """
        results = {}
        for doc_id, data_path in doc_mappings.items():
            results[doc_id] = self.load_document(doc_id, data_path)
        return results
    
    def is_ready(self) -> bool:
        """Check if the farm is ready (has data and tools initialized)."""
        return (self.silo.is_loaded() and 
                self.sickle is not None and 
                self.pitchfork is not None)
    
    # ==================== SEARCH METHODS (Sickle) ====================
    
    def search(self, query: str, search_type: str = "all", limit: int = 10) -> List[SearchResult]:
        """
        Search for content using the sickle.
        
        Args:
            query: Search query string
            search_type: Type of search ("all", "pages", "tables", "titles")
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.is_ready() or self.sickle is None:
            raise ValueError("Farm not ready. Load documents first.")
        
        return self.sickle.search(query, search_type, limit)
    
    def search_by_keywords(self, keywords: List[str], search_type: str = "all", limit: int = 10) -> List[SearchResult]:
        """
        Search using specific keywords.
        
        Args:
            keywords: List of keywords to search for
            search_type: Type of search ("all", "pages", "tables", "titles")
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.is_ready() or self.sickle is None:
            raise ValueError("Farm not ready. Load documents first.")
        
        return self.sickle.search_by_keywords(keywords, search_type, limit)
    
    def get_page_by_number(self, page_number: int, doc_id: Optional[str] = None) -> Optional[SearchResult]:
        """
        Get page by page number (for PDF highlighting).
        
        Args:
            page_number: Page number to retrieve
            doc_id: Optional document ID for disambiguation
            
        Returns:
            SearchResult for the page, or None if not found
        """
        if not self.is_ready() or self.sickle is None:
            raise ValueError("Farm not ready. Load documents first.")
        
        return self.sickle.get_page_by_number(page_number, doc_id)
    
    def get_available_keywords(self) -> List[str]:
        """Get all available keywords in the search index."""
        if not self.is_ready() or self.sickle is None:
            return []
        
        return self.sickle.get_available_keywords()
    
    # ==================== TABLE METHODS (Pitchfork) ====================
    
    def get_table_catalog(self) -> List[TableInfo]:
        """
        Get catalog of all available tables.
        
        Returns:
            List of TableInfo objects
        """
        if not self.is_ready() or self.pitchfork is None:
            return []
        
        return self.pitchfork.get_table_catalog()
    
    def get_table_by_id(self, table_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get complete table data by ID.
        
        Args:
            table_id: Table identifier
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Complete table data or None if not found
        """
        if not self.is_ready() or self.pitchfork is None:
            return None
        
        return self.pitchfork.get_table_by_id(table_id, doc_id)
    
    def get_tables_by_category(self, category: str) -> List[TableInfo]:
        """
        Get tables by technical category.
        
        Args:
            category: Technical category to filter by
            
        Returns:
            List of TableInfo objects matching the category
        """
        if not self.is_ready() or self.pitchfork is None:
            return []
        
        return self.pitchfork.get_tables_by_category(category)
    
    def get_tables_by_document(self, doc_id: str) -> List[TableInfo]:
        """
        Get all tables from a specific document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of TableInfo objects from the document
        """
        if not self.is_ready() or self.pitchfork is None:
            return []
        
        return self.pitchfork.get_tables_by_document(doc_id)
    
    def get_table_rows(self, table_id: str, criteria: Optional[Dict[str, Any]] = None, 
                      doc_id: Optional[str] = None) -> List[TableRow]:
        """
        Get table rows with optional filtering criteria.
        
        Args:
            table_id: Table identifier
            criteria: Optional filtering criteria
            doc_id: Optional document ID for disambiguation
            
        Returns:
            List of TableRow objects
        """
        if not self.is_ready() or self.pitchfork is None:
            return []
        
        return self.pitchfork.get_table_rows(table_id, criteria, doc_id)
    
    def search_table_values(self, table_id: str, search_term: str, 
                           doc_id: Optional[str] = None) -> List[TableRow]:
        """
        Search for specific values within a table.
        
        Args:
            table_id: Table identifier
            search_term: Term to search for
            doc_id: Optional document ID for disambiguation
            
        Returns:
            List of TableRow objects containing the search term
        """
        if not self.is_ready() or self.pitchfork is None:
            return []
        
        return self.pitchfork.search_table_values(table_id, search_term, doc_id)
    
    def get_table_statistics(self, table_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive statistics about a table.
        
        Args:
            table_id: Table identifier
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Table statistics or None if not found
        """
        if not self.is_ready() or self.pitchfork is None:
            return None
        
        return self.pitchfork.get_table_statistics(table_id, doc_id)
    
    # ==================== CONVENIENCE METHODS ====================
    
    # Removed domain-specific compatibility tables method
    
    # Removed domain-specific table methods - use get_tables_by_category() instead
    
    def get_document_info(self, doc_id: Optional[str] = None) -> Union[Dict[str, Any], None]:
        """
        Get document information.
        
        Args:
            doc_id: Specific document ID, or None for all documents
            
        Returns:
            Document information or None if not found
        """
        result = self.silo.get_document_info(doc_id)
        if result is None:
            return None
        elif isinstance(result, dict):
            return result
        else:
            # Convert DocumentInfo to dict
            return {
                "doc_id": result.doc_id,
                "title": result.title,
                "loaded_at": result.loaded_at.isoformat(),
                "page_count": result.page_count,
                "table_count": result.table_count,
                "keywords": result.keywords
            }
    
    def get_document_ids(self) -> List[str]:
        """Get list of all loaded document IDs."""
        return self.silo.get_document_ids()
    
    def get_all_keywords(self) -> List[str]:
        """Get all unique keywords across all documents."""
        return self.silo.get_all_keywords()
    
    # ==================== STATISTICS AND OVERVIEW ====================
    
    def get_farm_stats(self) -> FarmStats:
        """
        Get comprehensive statistics about the farm.
        
        Returns:
            FarmStats object with all statistics
        """
        silo_stats = self.silo.get_statistics()
        sickle_stats = self.sickle.get_index_stats() if self.sickle else {}
        pitchfork_stats = self.pitchfork.get_catalog_statistics() if self.pitchfork else {}
        
        return FarmStats(
            silo_stats=silo_stats,
            sickle_stats=sickle_stats,
            pitchfork_stats=pitchfork_stats,
            total_documents=silo_stats.get("total_documents", 0),
            total_pages=silo_stats.get("total_pages", 0),
            total_tables=silo_stats.get("total_tables", 0),
            total_keywords=silo_stats.get("total_keywords", 0)
        )
    
    def get_data_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive overview of all loaded data.
        
        Returns:
            Dictionary with data overview
        """
        if not self.is_ready():
            return {"error": "Farm not ready. Load documents first."}
        
        # Get basic stats
        farm_stats = self.get_farm_stats()
        
        # Get sample data
        sample_keywords = self.get_available_keywords()[:20]
        sample_tables = self.get_table_catalog()[:5]
        
        # Get document details
        doc_info = self.get_document_info()
        
        return {
            "statistics": {
                "total_documents": farm_stats.total_documents,
                "total_pages": farm_stats.total_pages,
                "total_tables": farm_stats.total_tables,
                "total_keywords": farm_stats.total_keywords
            },
            "documents": doc_info,
            "sample_keywords": sample_keywords,
            "sample_tables": [
                {
                    "table_id": table.table_id,
                    "title": table.title,
                    "category": table.technical_category,
                    "doc_id": table.doc_id
                }
                for table in sample_tables
            ],
            "tools_ready": {
                "silo": self.silo.is_loaded(),
                "sickle": self.sickle is not None,
                "pitchfork": self.pitchfork is not None,
                "scythe": self.scythe is not None
            }
        }
    
    # ==================== MAINTENANCE METHODS ====================
    
    def refresh_indexes(self):
        """Rebuild all indexes and catalogs."""
        if self.sickle:
            self.sickle.build_index()
        
        if self.pitchfork:
            self.pitchfork.build_catalog()
    
    def clear_farm(self):
        """Clear all data and reset tools."""
        self.silo.clear()
        self.sickle = None
        self.pitchfork = None
        self.scythe = None
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a specific document and refresh indexes.
        
        Args:
            doc_id: Document ID to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        success = self.silo.remove_document(doc_id)
        
        if success and self.is_ready():
            self.refresh_indexes()
        
        return success 