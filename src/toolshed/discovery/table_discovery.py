"""
Table Discovery Tool

Provides overview of all available tables in the system.
Returns table titles, categories, and page numbers for initial exploration.
"""

from typing import List, Dict, Any
from src.silo import Silo


class TableDiscovery:
    """
    Discovery tool for understanding available tables.
    
    Provides high-level overview of all tables in the system,
    including titles, categories, and page numbers for initial exploration.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize table discovery with a silo of data.
        
        Args:
            silo: Silo instance containing the data to explore
        """
        self.silo = silo
        self._table_cache: List[Dict[str, Any]] = []
        self._is_cached = False
    
    def view_tables(self) -> List[Dict[str, Any]]:
        """
        Get overview of all available tables.
        
        Returns:
            List of dictionaries containing table information:
            [
                {
                    "table_title": str,
                    "category": str,
                    "page_number": int,
                    "doc_id": str,
                    "row_count": int,
                    "column_count": int
                },
                ...
            ]
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        if not self._is_cached:
            self._build_table_cache()
        
        return self._table_cache
    
    def _build_table_cache(self):
        """
        Build cache of all tables from silo data.
        
        Extracts table information from all pages and organizes
        it for easy discovery and exploration.
        """
        self._table_cache.clear()
        
        # Get all pages from silo
        pages = self.silo.get_all_pages()
        
        for page in pages:
            page_id = page["page_id"]
            page_number = self._extract_page_number(page_id)
            
            # Process tables in this page
            for table in page.get("tables", []):
                table_info = self._extract_table_info(table, page, page_number)
                if table_info:
                    self._table_cache.append(table_info)
        
        # Sort by page number, then by table title for consistent ordering
        self._table_cache.sort(key=lambda x: (x["page_number"] or 0, x["table_title"]))
        self._is_cached = True
    
    def _extract_table_info(self, table: dict, page: dict, page_number: int) -> Dict[str, Any] | None:
        """
        Extract table information from table data.
        
        Args:
            table: Table dictionary
            page: Page dictionary containing the table
            page_number: Page number
            
        Returns:
            Dictionary with table information or None if invalid
        """
        if not table or "title" not in table:
            return None
        
        # Get table dimensions
        rows = table.get("rows", [])
        columns = table.get("columns", [])
        
        # Extract category from metadata
        category = "Unknown"
        if "metadata" in table and "technical_category" in table["metadata"]:
            category = table["metadata"]["technical_category"]
        
        return {
            "table_title": table["title"],
            "category": category,
            "page_number": page_number,
            "doc_id": page["doc_id"],
            "row_count": len(rows),
            "column_count": len(columns),
            "description": table.get("description", "")
        }
    
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