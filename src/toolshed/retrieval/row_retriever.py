"""
Row Retriever Tool

Retrieves specific rows from tables based on column value matching.
Returns rows where row[column] = target for precise data extraction.
"""

from typing import Dict, Any, Optional, List
from src.silo import Silo


class RowRetriever:
    """
    Retrieval tool for getting specific rows from tables.
    
    Provides access to rows that match specific criteria,
    enabling precise data extraction from tables.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize row retriever with a silo of data.
        
        Args:
            silo: Silo instance containing the data to retrieve
        """
        self.silo = silo
    
    def get_row_data(self, table_name: str, column: str, target: str) -> Optional[Dict[str, Any]]:
        """
        Get rows where the specified column matches the target value.
        
        Args:
            table_name: Name/title of the table to search
            column: Column name to match against
            target: Target value to match (case-insensitive)
            
        Returns:
            Dictionary containing matching rows or None if not found:
            {
                "table_title": str,
                "column": str,
                "target": str,
                "matching_rows": [dict],
                "row_count": int,
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
        
        # Get columns and rows
        columns = table_data.get("columns", [])
        rows = table_data.get("rows", [])
        
        # Validate that the column exists
        available_columns = [col.get("name", "Unknown") for col in columns]
        if column not in available_columns:
            raise ValueError(f"Column '{column}' not found in table. Available columns: {available_columns}")
        
        # Find matching rows (case-insensitive)
        target_lower = str(target).lower()
        matching_rows = []
        
        for row in rows:
            if isinstance(row, dict) and column in row:
                row_value = str(row[column]).lower()
                if row_value == target_lower:
                    matching_rows.append(row)
        
        return {
            "table_title": table_data["title"],
            "column": column,
            "target": target,
            "matching_rows": matching_rows,
            "row_count": len(matching_rows),
            "page_number": page_number,
            "description": table_data.get("description", ""),
            "category": table_data.get("metadata", {}).get("technical_category", "Unknown")
        }
    
    def get_rows_by_multiple_criteria(self, table_name: str, criteria: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Get rows that match multiple column criteria.
        
        Args:
            table_name: Name/title of the table to search
            criteria: Dictionary of {column: target_value} pairs
            
        Returns:
            Dictionary containing matching rows or None if not found:
            {
                "table_title": str,
                "criteria": dict,
                "matching_rows": [dict],
                "row_count": int,
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
        
        # Get columns and rows
        columns = table_data.get("columns", [])
        rows = table_data.get("rows", [])
        
        # Validate that all criteria columns exist
        available_columns = [col.get("name", "Unknown") for col in columns]
        missing_columns = [col for col in criteria.keys() if col not in available_columns]
        if missing_columns:
            raise ValueError(f"Columns not found in table: {missing_columns}. Available columns: {available_columns}")
        
        # Find matching rows (all criteria must match)
        matching_rows = []
        
        for row in rows:
            if isinstance(row, dict):
                all_criteria_match = True
                for column, target in criteria.items():
                    if column not in row:
                        all_criteria_match = False
                        break
                    
                    row_value = str(row[column]).lower()
                    target_lower = str(target).lower()
                    if row_value != target_lower:
                        all_criteria_match = False
                        break
                
                if all_criteria_match:
                    matching_rows.append(row)
        
        return {
            "table_title": table_data["title"],
            "criteria": criteria,
            "matching_rows": matching_rows,
            "row_count": len(matching_rows),
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