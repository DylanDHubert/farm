"""
Page Discovery Tool

Provides overview of all available pages in the system.
Returns page numbers and titles for initial data exploration.
"""

from typing import List, Dict, Any
from src.silo import Silo


class PageDiscovery:
    """
    Discovery tool for understanding available pages.
    
    Provides high-level overview of all pages in the system,
    including page numbers and titles for initial exploration.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize page discovery with a silo of data.
        
        Args:
            silo: Silo instance containing the data to explore
        """
        self.silo = silo
    
    def view_pages(self) -> List[Dict[str, Any]]:
        """
        Get overview of all available pages.
        
        Returns:
            List of dictionaries containing page information:
            [
                {
                    "page_number": int,
                    "page_title": str,
                    "doc_id": str
                },
                ...
            ]
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        pages = self.silo.get_all_pages()
        overview = []
        
        for page in pages:
            page_id = page["page_id"]
            page_number = self._extract_page_number(page_id)
            page_title = page.get("title", f"Page {page_number}")
            
            overview.append({
                "page_number": page_number,
                "page_title": page_title,
                "doc_id": page["doc_id"]
            })
        
        # Sort by page number for consistent ordering
        overview.sort(key=lambda x: x["page_number"] or 0)
        return overview
    
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