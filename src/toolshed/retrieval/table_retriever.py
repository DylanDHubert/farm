"""
Table Retriever Tool

Retrieves table data with optional column filtering.
Returns actual table data for specific analysis and extraction.
"""

from typing import Dict, Any, Optional, List, Union
from src.silo import Silo


class TableRetriever:
    """
    Retrieval tool for getting table data.
    
    Provides access to actual table data with optional
    column filtering for specific data extraction.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize table retriever with a silo of data.
        
        Args:
            silo: Silo instance containing the data to retrieve
        """
        self.silo = silo
    
    def get_table_data(self, table_name: str, columns: Union[str, List[str]] = "all") -> Optional[Dict[str, Any]]:
        """
        Get table data with optional column filtering.
        
        Args:
            table_name: Name/title of the table to retrieve
            columns: "all" or list of column names to include
            
        Returns:
            Dictionary containing table data or None if not found:
            {
                "table_title": str,
                "columns": [str],
                "rows": [dict],
                "row_count": int,
                "column_count": int,
                "page_number": int
            }
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        # Get table data by title
        table_data = self.silo.get_table_by_title(table_name)
        if not table_data:
            return None
        
        # Extract page information
        page_id = table_data["page_id"]
        page_number = self._extract_page_number(page_id)
        
        # Get original columns and rows
        original_columns = table_data.get("columns", [])
        original_rows = table_data.get("rows", [])
        
        # Process columns based on filter
        if columns == "all":
            # Get all column names
            column_names = [col.get("name", "Unknown") for col in original_columns]
            filtered_rows = original_rows
        else:
            # Filter by specific columns
            if not isinstance(columns, list):
                raise ValueError("columns must be 'all' or a list of column names")
            
            # Validate that requested columns exist
            available_columns = [col.get("name", "Unknown") for col in original_columns]
            missing_columns = [col for col in columns if col not in available_columns]
            if missing_columns:
                raise ValueError(f"Columns not found in table: {missing_columns}")
            
            column_names = columns
            
            # Filter rows to only include requested columns
            filtered_rows = []
            for row in original_rows:
                if isinstance(row, dict):
                    filtered_row = {col: row.get(col, "") for col in column_names}
                    filtered_rows.append(filtered_row)
                else:
                    # Handle case where row is not a dict
                    filtered_rows.append(row)
        
        return {
            "table_title": table_data["title"],
            "columns": column_names,
            "rows": filtered_rows,
            "row_count": len(filtered_rows),
            "column_count": len(column_names),
            "page_number": page_number,
            "description": table_data.get("description", ""),
            "category": table_data.get("metadata", {}).get("technical_category", "Unknown")
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