"""
Keyword Discovery Tool

Provides overview of all available keywords in the system.
Returns comprehensive list of keywords for content exploration.
"""

from typing import List, Set
from src.silo import Silo


class KeywordDiscovery:
    """
    Discovery tool for understanding available keywords.
    
    Provides comprehensive list of all keywords in the system
    for initial content exploration and understanding.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize keyword discovery with a silo of data.
        
        Args:
            silo: Silo instance containing the data to explore
        """
        self.silo = silo
        self._keywords_cache: Set[str] = set()
        self._is_cached = False
    
    def view_keywords(self) -> List[str]:
        """
        Get overview of all available keywords.
        
        Returns:
            List of all unique keywords found in the system
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        if not self._is_cached:
            self._build_keyword_cache()
        
        # Return sorted list for consistent ordering
        return sorted(list(self._keywords_cache))
    
    def _build_keyword_cache(self):
        """
        Build cache of all keywords from silo data.
        
        Extracts keywords from pages, tables, and metadata
        to create a comprehensive keyword index.
        """
        self._keywords_cache.clear()
        
        # Get all pages from silo
        pages = self.silo.get_all_pages()
        
        for page in pages:
            # Extract keywords from page content
            self._extract_keywords_from_text(page.get("content", ""))
            
            # Extract keywords from page metadata
            if "metadata" in page:
                self._extract_keywords_from_metadata(page["metadata"])
            
            # Extract keywords from tables
            for table in page.get("tables", []):
                self._extract_keywords_from_table(table)
        
        self._is_cached = True
    
    def _extract_keywords_from_text(self, text: str):
        """
        Extract keywords from text content.
        
        Args:
            text: Text content to extract keywords from
        """
        if not text:
            return
        
        # Simple keyword extraction - split on whitespace and filter
        words = text.lower().split()
        keywords = [word.strip('.,!?;:()[]{}"\'') for word in words]
        keywords = [word for word in keywords if len(word) > 2 and word.isalnum()]
        
        self._keywords_cache.update(keywords)
    
    def _extract_keywords_from_metadata(self, metadata: dict):
        """
        Extract keywords from metadata.
        
        Args:
            metadata: Metadata dictionary
        """
        if not metadata:
            return
        
        # Extract keywords from metadata fields
        for value in metadata.values():
            if isinstance(value, str):
                self._extract_keywords_from_text(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        self._extract_keywords_from_text(item)
    
    def _extract_keywords_from_table(self, table: dict):
        """
        Extract keywords from table data.
        
        Args:
            table: Table dictionary
        """
        if not table:
            return
        
        # Extract from table title and description
        self._extract_keywords_from_text(table.get("title", ""))
        self._extract_keywords_from_text(table.get("description", ""))
        
        # Extract from column names
        for column in table.get("columns", []):
            if isinstance(column, dict):
                self._extract_keywords_from_text(column.get("name", ""))
            elif isinstance(column, str):
                self._extract_keywords_from_text(column)
        
        # Extract from table metadata
        if "metadata" in table:
            self._extract_keywords_from_metadata(table["metadata"])
        
        # Extract from sample row data
        for row in table.get("rows", [])[:5]:  # Limit to first 5 rows for performance
            if isinstance(row, dict):
                for value in row.values():
                    if isinstance(value, str):
                        self._extract_keywords_from_text(value) 