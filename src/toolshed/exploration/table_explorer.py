"""
Table Explorer Tool

Provides detailed exploration of specific tables.
Returns table metadata, columns, and sample data for understanding table structure.
"""

from typing import Dict, Any, Optional, List
from src.silo import Silo


class TableExplorer:
    """
    Exploration tool for understanding specific tables.
    
    Provides detailed table summaries including metadata,
    column information, and sample data for exploration.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize table explorer with a silo of data.
        
        Args:
            silo: Silo instance containing the data to explore
        """
        self.silo = silo
    
    def table_summary(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed summary of a specific table.
        
        Args:
            table_name: Name/title of the table to explore
            
        Returns:
            Dictionary containing table summary or None if not found:
            {
                "table_title": str,
                "description": str,
                "category": str,
                "page_number": int,
                "row_count": int,
                "column_count": int,
                "columns": [{"name": str, "data_type": str, "sample_values": [str]}],
                "sample_rows": [dict],
                "metadata": dict
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
        
        # Get table dimensions
        rows = table_data.get("rows", [])
        columns = table_data.get("columns", [])
        
        # Extract category from metadata
        category = "Unknown"
        if "metadata" in table_data and "technical_category" in table_data["metadata"]:
            category = table_data["metadata"]["technical_category"]
        
        # Process columns with sample values
        processed_columns = []
        for col in columns:
            col_info = {
                "name": col.get("name", "Unknown"),
                "data_type": col.get("data_type", "string")
            }
            
            # Get sample values from first few rows
            sample_values = []
            for row in rows[:3]:  # Sample from first 3 rows
                if isinstance(row, dict) and col_info["name"] in row:
                    value = str(row[col_info["name"]])
                    if value not in sample_values:
                        sample_values.append(value)
                        if len(sample_values) >= 3:  # Limit to 3 sample values
                            break
            
            col_info["sample_values"] = sample_values
            processed_columns.append(col_info)
        
        # Get sample rows (first 3)
        sample_rows = rows[:3] if rows else []
        
        return {
            "table_title": table_data["title"],
            "description": table_data.get("description", ""),
            "category": category,
            "page_number": page_number,
            "row_count": len(rows),
            "column_count": len(columns),
            "columns": processed_columns,
            "sample_rows": sample_rows,
            "metadata": table_data.get("metadata", {})
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