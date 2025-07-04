"""
Page Retriever Tool

Retrieves specific page content by title or number.
Returns full page content for detailed analysis and extraction.
"""

from typing import Dict, Any, Optional, Union
from src.silo import Silo


class PageRetriever:
    """
    Retrieval tool for getting page content.
    
    Provides access to specific page content by title or number,
    enabling detailed page-level analysis and extraction.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize page retriever with a silo of data.
        
        Args:
            silo: Silo instance containing the data to retrieve
        """
        self.silo = silo
        self._page_cache: Dict[str, Dict[str, Any]] = {}
        self._is_cached = False
    
    def get_page_content(self, page_identifier: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get page content by title or number.
        
        Args:
            page_identifier: Page title (str) or page number (int)
            
        Returns:
            Dictionary containing page content or None if not found:
            {
                "page_title": str,
                "page_number": int,
                "content": str,
                "tables": [dict],
                "table_count": int,
                "doc_id": str
            }
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        if not self._is_cached:
            self._build_page_cache()
        
        # Try to find page by identifier
        page_data = None
        
        if isinstance(page_identifier, int):
            # Search by page number
            page_data = self._find_page_by_number(page_identifier)
        else:
            # Search by title
            page_data = self._find_page_by_title(page_identifier)
        
        if not page_data:
            return None
        
        # Extract page information
        page_id = page_data["page_id"]
        page_number = self._extract_page_number(page_id)
        tables = page_data.get("tables", [])
        
        return {
            "page_title": page_data.get("title", f"Page {page_number}"),
            "page_number": page_number,
            "content": page_data.get("content", ""),
            "tables": tables,
            "table_count": len(tables),
            "doc_id": page_data["doc_id"],
            "metadata": page_data.get("metadata", {})
        }
    
    def get_page_by_number(self, page_number: int) -> Optional[Dict[str, Any]]:
        """
        Get page content by page number.
        
        Args:
            page_number: Page number to retrieve
            
        Returns:
            Dictionary containing page content or None if not found
        """
        return self.get_page_content(page_number)
    
    def get_page_by_title(self, page_title: str) -> Optional[Dict[str, Any]]:
        """
        Get page content by page title.
        
        Args:
            page_title: Page title to retrieve
            
        Returns:
            Dictionary containing page content or None if not found
        """
        return self.get_page_content(page_title)
    
    def _build_page_cache(self):
        """Build cache of pages for efficient searching."""
        self._page_cache.clear()
        
        # Get all pages from silo
        pages = self.silo.get_all_pages()
        
        for page in pages:
            page_id = page["page_id"]
            page_number = self._extract_page_number(page_id)
            page_title = page.get("title", f"Page {page_number}")
            
            # Cache by both number and title
            self._page_cache[f"number_{page_number}"] = page
            self._page_cache[f"title_{page_title.lower()}"] = page
        
        self._is_cached = True
    
    def _find_page_by_number(self, page_number: int) -> Optional[Dict[str, Any]]:
        """Find page by page number."""
        cache_key = f"number_{page_number}"
        return self._page_cache.get(cache_key)
    
    def _find_page_by_title(self, page_title: str) -> Optional[Dict[str, Any]]:
        """Find page by page title (case-insensitive)."""
        cache_key = f"title_{page_title.lower()}"
        return self._page_cache.get(cache_key)
    
    def _extract_page_number(self, page_id: str) -> int:
        """
        Extract page number from page_id.
        
        Args:
            page_id: Page identifier (e.g., "page_1", "page_10")
            
        Returns:
            Page number as integer
        """
        try:
            # Extract number from page_id (e.g., "page_1" -> 1)
            return int(page_id.split("_")[-1])
        except (ValueError, IndexError):
            # Fallback: try to extract any number from the string
            import re
            numbers = re.findall(r'\d+', page_id)
            return int(numbers[0]) if numbers else 0 