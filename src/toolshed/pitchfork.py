"""
Pitchfork - Table Data Access for PB&J Data

A specialized tool for organizing and retrieving table data like a pitchfork
organizes hay into neat piles. Provides comprehensive table access, filtering,
and organization capabilities across multiple documents.
"""

from typing import Dict, List, Optional, Any, Union
from silo import Silo
from src.models.table import TableInfo, TableRow
from src.models.search import SearchResult


class Pitchfork:
    """
    Table data access tool for PB&J data.
    
    Provides comprehensive table access, filtering, and organization capabilities
    across multiple documents. Like a pitchfork organizing hay into neat piles.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize the pitchfork with a silo of data.
        
        Args:
            silo: Silo instance containing the data to access
        """
        self.silo = silo
        self.table_catalog: Dict[str, TableInfo] = {}
        self.is_cataloged = False
    
    def build_catalog(self):
        """Build comprehensive table catalog from silo data."""
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo for cataloging")
        
        self.table_catalog.clear()
        
        # Get all tables from silo
        tables = self.silo.get_all_tables()
        
        for table in tables:
            # Use table title as unique identifier instead of table_id
            # since table_ids are duplicated across pages but titles are unique
            unique_id = table["title"]
            original_table_id = table["table_id"]
            doc_id = table["doc_id"]
            page_id = table["page_id"]
            
            # Extract page number
            page_number = self._extract_page_number(page_id)
            
            # Get table dimensions
            rows = table.get("rows", [])
            row_count = len(rows)
            column_count = len(table.get("columns", []))
            
            # Extract data types from columns
            data_types = []
            for col in table.get("columns", []):
                if "data_type" in col:
                    data_types.append(col["data_type"])
            
            # Create table info with unique_id as the key
            self.table_catalog[unique_id] = TableInfo(
                table_id=original_table_id,  # Keep original table_id for compatibility
                title=table["title"],
                description=table["description"],
                doc_id=doc_id,
                page_id=page_id,
                page_number=page_number,
                row_count=row_count,
                column_count=column_count,
                technical_category=table["metadata"]["technical_category"],
                data_types=data_types
            )
        
        self.is_cataloged = True
    
    def get_table_catalog(self) -> List[TableInfo]:
        """
        Get catalog of all available tables.
        
        Returns:
            List of TableInfo objects
        """
        if not self.is_cataloged:
            self.build_catalog()
        return list(self.table_catalog.values())
    
    def get_table_by_id(self, table_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get complete table data by ID or title.
        
        Args:
            table_id: Table identifier or title
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Complete table data or None if not found
        """
        # First try to get by title (our unique identifier)
        result = self.silo.get_table_by_title(table_id, doc_id)
        if result:
            return result
        
        # Fallback to original table_id lookup
        return self.silo.get_table_by_id(table_id, doc_id)
    
    def get_table_info(self, table_id: str) -> Optional[TableInfo]:
        """
        Get table information from catalog.
        
        Args:
            table_id: Table identifier or title
            
        Returns:
            TableInfo object or None if not found
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        # First try to find by title (our unique identifier)
        if table_id in self.table_catalog:
            return self.table_catalog[table_id]
        
        # Fallback: search by table_id in case someone passes the original table_id
        for info in self.table_catalog.values():
            if info.table_id == table_id:
                return info
        
        return None
    
    def get_table_by_title(self, title: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get complete table data by title.
        
        Args:
            title: Table title
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Complete table data or None if not found
        """
        return self.silo.get_table_by_title(title, doc_id)
    
    def get_tables_by_category(self, category: str) -> List[TableInfo]:
        """
        Get tables by technical category.
        
        Args:
            category: Technical category to filter by
            
        Returns:
            List of TableInfo objects matching the category
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        category_lower = category.lower()
        return [
            info for info in self.table_catalog.values()
            if category_lower in info.technical_category.lower()
        ]
    
    def get_tables_by_document(self, doc_id: str) -> List[TableInfo]:
        """
        Get all tables from a specific document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of TableInfo objects from the document
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        return [
            info for info in self.table_catalog.values()
            if info.doc_id == doc_id
        ]
    
    def get_tables_by_page(self, page_id: str) -> List[TableInfo]:
        """
        Get all tables from a specific page.
        
        Args:
            page_id: Page identifier
            
        Returns:
            List of TableInfo objects from the page
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        return [
            info for info in self.table_catalog.values()
            if info.page_id == page_id
        ]
    
    def get_tables_by_keyword(self, keyword: str) -> List[TableInfo]:
        """
        Find tables containing specific keyword.
        
        Args:
            keyword: Keyword to search for
        
        Returns:
            List of TableInfo objects containing the keyword.
            If no matches are found, returns the full table catalog as a fallback so the agent can see all options.
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        keyword_lower = keyword.lower()
        matches = []
        
        for info in self.table_catalog.values():
            if (keyword_lower in info.title.lower() or 
                keyword_lower in info.description.lower() or
                keyword_lower in info.technical_category.lower()):
                matches.append(info)
        
        if matches:
            return matches
        # Fallback: return all tables if no match
        return list(self.table_catalog.values())
    
    def get_tables_by_data_type(self, data_type: str) -> List[TableInfo]:
        """
        Get tables containing specific data types.
        
        Args:
            data_type: Data type to search for
            
        Returns:
            List of TableInfo objects containing the data type
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        data_type_lower = data_type.lower()
        return [
            info for info in self.table_catalog.values()
            if any(data_type_lower in dt.lower() for dt in info.data_types)
        ]
    
    # Removed domain-specific compatibility tables method
    
    # Removed domain-specific table methods - use get_tables_by_category() instead
    
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
        table_data = self.silo.get_table_by_id(table_id, doc_id)
        if not table_data:
            return []
        
        rows = []
        for i, row_data in enumerate(table_data.get("rows", [])):
            # Apply filtering criteria if provided
            if criteria and not self._row_matches_criteria(row_data, criteria):
                continue
            
            rows.append(TableRow(
                row_index=i,
                data=row_data,
                table_id=table_id,
                doc_id=table_data["doc_id"],
                page_id=table_data["page_id"]
            ))
        
        return rows
    
    def get_table_columns(self, table_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get table column information.
        
        Args:
            table_id: Table identifier
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Column information or None if not found
        """
        table_data = self.silo.get_table_by_id(table_id, doc_id)
        if not table_data:
            return None
        
        return {
            "columns": table_data.get("columns", []),
            "table_id": table_id,
            "doc_id": table_data["doc_id"],
            "page_id": table_data["page_id"]
        }
    
    def search_table_values(self, table_id: str, search_term: str, 
                           doc_id: Optional[str] = None) -> List[TableRow]:
        """
        Search for specific values within a table.
        
        Args:
            table_id: Table identifier or title
            search_term: Term to search for
            doc_id: Optional document ID for disambiguation
            
        Returns:
            List of TableRow objects containing the search term
        """
        # First try to get by title (our unique identifier)
        table_data = self.silo.get_table_by_title(table_id, doc_id)
        if not table_data:
            # Fallback to original table_id lookup
            table_data = self.silo.get_table_by_id(table_id, doc_id)
        
        if not table_data:
            return []
        
        search_term_lower = search_term.lower()
        matches = []
        
        for i, row_data in enumerate(table_data.get("rows", [])):
            # Search in all row values
            for value in row_data.values():
                if isinstance(value, str) and search_term_lower in value.lower():
                    matches.append(TableRow(
                        row_index=i,
                        data=row_data,
                        table_id=table_data["table_id"],  # Use actual table_id from data
                        doc_id=table_data["doc_id"],
                        page_id=table_data["page_id"]
                    ))
                    break  # Found match in this row, move to next
        
        return matches
    
    def table_exists(self, table_id: str, doc_id: Optional[str] = None) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_id: Table identifier
            doc_id: Optional document ID for disambiguation
            
        Returns:
            True if table exists, False otherwise
        """
        return self.silo.get_table_by_id(table_id, doc_id) is not None
    
    def get_table_statistics(self, table_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive statistics about a table.
        
        Args:
            table_id: Table identifier
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Table statistics or None if not found
        """
        table_data = self.silo.get_table_by_id(table_id, doc_id)
        if not table_data:
            return None
        
        rows = table_data.get("rows", [])
        columns = table_data.get("columns", [])
        
        # Calculate basic statistics
        row_count = len(rows)
        column_count = len(columns)
        
        # Calculate value statistics for each column
        column_stats = {}
        for col in columns:
            col_name = col.get("name", "")
            if col_name and rows:
                values = [row.get(col_name) for row in rows if col_name in row]
                non_null_values = [v for v in values if v is not None and v != ""]
                
                column_stats[col_name] = {
                    "total_values": len(values),
                    "non_null_values": len(non_null_values),
                    "null_count": len(values) - len(non_null_values),
                    "unique_values": len(set(non_null_values)) if non_null_values else 0
                }
        
        return {
            "table_id": table_id,
            "doc_id": table_data["doc_id"],
            "page_id": table_data["page_id"],
            "title": table_data["title"],
            "row_count": row_count,
            "column_count": column_count,
            "column_statistics": column_stats,
            "technical_category": table_data["metadata"]["technical_category"]
        }
    
    def get_catalog_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the table catalog.
        
        Returns:
            Dictionary with catalog statistics
        """
        if not self.is_cataloged:
            self.build_catalog()
        
        total_tables = len(self.table_catalog)
        total_rows = sum(info.row_count for info in self.table_catalog.values())
        total_columns = sum(info.column_count for info in self.table_catalog.values())
        
        # Count by category
        categories = {}
        for info in self.table_catalog.values():
            cat = info.technical_category
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count by document
        documents = {}
        for info in self.table_catalog.values():
            doc = info.doc_id
            documents[doc] = documents.get(doc, 0) + 1
        
        return {
            "total_tables": total_tables,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "categories": categories,
            "documents": documents,
            "is_cataloged": self.is_cataloged
        }
    
    # ==================== PRIVATE METHODS ====================
    
    def _extract_page_number(self, page_id: str) -> Optional[int]:
        """Extract page number from page_id."""
        import re
        match = re.search(r'page_(\d+)', page_id)
        return int(match.group(1)) if match else None
    
    def _row_matches_criteria(self, row_data: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if a row matches the given criteria."""
        for field, value in criteria.items():
            if field not in row_data:
                return False
            
            row_value = row_data[field]
            
            # Handle different comparison types
            if isinstance(value, dict):
                # Complex criteria like {"operator": "contains", "value": "text"}
                operator = value.get("operator", "equals")
                target_value = value.get("value")
                
                if operator == "equals":
                    if row_value != target_value:
                        return False
                elif operator == "contains":
                    if isinstance(row_value, str) and isinstance(target_value, str):
                        if target_value.lower() not in row_value.lower():
                            return False
                    else:
                        return False
                elif operator == "greater_than":
                    if not (isinstance(row_value, (int, float)) and isinstance(target_value, (int, float)) and row_value > target_value):
                        return False
                elif operator == "less_than":
                    if not (isinstance(row_value, (int, float)) and isinstance(target_value, (int, float)) and row_value < target_value):
                        return False
            else:
                # Simple equality check
                if row_value != value:
                    return False
        
        return True 