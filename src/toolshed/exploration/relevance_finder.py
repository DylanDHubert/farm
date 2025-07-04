"""
Relevance Finder Tool

Finds relevant tables and pages based on search queries.
Uses multiple criteria: keywords, columns, rows, categories, and values.
"""

from typing import List, Dict, Any, Set
from src.silo import Silo
import re


class RelevanceFinder:
    """
    Exploration tool for finding relevant tables and pages.
    
    Uses multiple relevance criteria to find tables and pages
    that match search queries: keywords, columns, rows, categories, values.
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize relevance finder with a silo of data.
        
        Args:
            silo: Silo instance containing the data to search
        """
        self.silo = silo
        self._table_cache: List[Dict[str, Any]] = []
        self._page_cache: List[Dict[str, Any]] = []
        self._is_cached = False
    
    def find_relevant_tables(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Find tables relevant to the search query.
        
        Args:
            search_query: Search query to find relevant tables for
            
        Returns:
            List of relevant tables with relevance information:
            [
                {
                    "table_name": str,
                    "relation": str,  # "page_keywords", "column", "row", "category", "values"
                    "relevance_score": float,  # 0.0 to 1.0
                    "page_number": int,
                    "category": str,
                    "match_details": str
                },
                ...
            ]
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        if not self._is_cached:
            self._build_caches()
        
        # Normalize search query
        query_tokens = self._tokenize_query(search_query.lower())
        if not query_tokens:
            return []
        
        relevant_tables = []
        
        for table_info in self._table_cache:
            relevance_info = self._calculate_table_relevance(table_info, query_tokens)
            if relevance_info["relevance_score"] > 0:
                relevant_tables.append(relevance_info)
        
        # Sort by relevance score (highest first)
        relevant_tables.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_tables
    
    def find_relevant_pages(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Find pages relevant to the search query.
        
        Args:
            search_query: Search query to find relevant pages for
            
        Returns:
            List of relevant pages with relevance information:
            [
                {
                    "page_title": str,
                    "page_number": int,
                    "relation": str,  # "keywords", "content", "table_titles"
                    "relevance_score": float,  # 0.0 to 1.0
                    "match_details": str
                },
                ...
            ]
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo")
        
        if not self._is_cached:
            self._build_caches()
        
        # Normalize search query
        query_tokens = self._tokenize_query(search_query.lower())
        if not query_tokens:
            return []
        
        relevant_pages = []
        
        for page_info in self._page_cache:
            relevance_info = self._calculate_page_relevance(page_info, query_tokens)
            if relevance_info["relevance_score"] > 0:
                relevant_pages.append(relevance_info)
        
        # Sort by relevance score (highest first)
        relevant_pages.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_pages
    
    def _build_caches(self):
        """Build caches of tables and pages for efficient searching."""
        self._table_cache.clear()
        self._page_cache.clear()
        
        # Get all pages from silo
        pages = self.silo.get_all_pages()
        
        for page in pages:
            page_id = page["page_id"]
            page_number = self._extract_page_number(page_id)
            
            # Cache page information
            page_info = {
                "page_title": page.get("title", f"Page {page_number}"),
                "page_number": page_number,
                "content": page.get("content", "").lower(),
                "keywords": self._extract_keywords_from_text(page.get("content", "")),
                "table_titles": []
            }
            
            # Process tables in this page
            for table in page.get("tables", []):
                table_info = self._extract_table_info(table, page, page_number)
                if table_info:
                    self._table_cache.append(table_info)
                    page_info["table_titles"].append(table["title"])
            
            self._page_cache.append(page_info)
        
        self._is_cached = True
    
    def _extract_table_info(self, table: dict, page: dict, page_number: int) -> Dict[str, Any] | None:
        """Extract comprehensive table information for relevance matching."""
        if not table or "title" not in table:
            return None
        
        rows = table.get("rows", [])
        columns = table.get("columns", [])
        
        # Extract category
        category = "Unknown"
        if "metadata" in table and "technical_category" in table["metadata"]:
            category = table["metadata"]["technical_category"]
        
        # Extract column names and sample values
        column_names = []
        sample_values = []
        for col in columns:
            col_name = col.get("name", "Unknown")
            column_names.append(col_name.lower())
            
            # Get sample values from first few rows
            for row in rows[:3]:
                if isinstance(row, dict) and col_name in row:
                    value = str(row[col_name]).lower()
                    if value not in sample_values:
                        sample_values.append(value)
        
        return {
            "table_name": table["title"],
            "page_number": page_number,
            "category": category.lower(),
            "column_names": column_names,
            "sample_values": sample_values,
            "row_count": len(rows),
            "description": table.get("description", "").lower()
        }
    
    def _calculate_table_relevance(self, table_info: Dict[str, Any], query_tokens: List[str]) -> Dict[str, Any]:
        """Calculate relevance score for a table based on multiple criteria."""
        max_score = 0.0
        best_relation = ""
        match_details = []
        
        # Check category relevance (highest weight)
        category_matches = sum(1 for token in query_tokens if token in table_info["category"])
        if category_matches > 0:
            score = min(category_matches / len(query_tokens), 1.0) * 0.8
            if score > max_score:
                max_score = score
                best_relation = "category"
                match_details.append(f"Category matches: {category_matches} tokens")
        
        # Check column name relevance
        column_matches = sum(1 for token in query_tokens if any(token in col for col in table_info["column_names"]))
        if column_matches > 0:
            score = min(column_matches / len(query_tokens), 1.0) * 0.6
            if score > max_score:
                max_score = score
                best_relation = "column"
                match_details.append(f"Column matches: {column_matches} tokens")
        
        # Check sample values relevance
        value_matches = sum(1 for token in query_tokens if any(token in val for val in table_info["sample_values"]))
        if value_matches > 0:
            score = min(value_matches / len(query_tokens), 1.0) * 0.4
            if score > max_score:
                max_score = score
                best_relation = "values"
                match_details.append(f"Value matches: {value_matches} tokens")
        
        # Check description relevance
        desc_matches = sum(1 for token in query_tokens if token in table_info["description"])
        if desc_matches > 0:
            score = min(desc_matches / len(query_tokens), 1.0) * 0.3
            if score > max_score:
                max_score = score
                best_relation = "description"
                match_details.append(f"Description matches: {desc_matches} tokens")
        
        return {
            "table_name": table_info["table_name"],
            "relation": best_relation,
            "relevance_score": max_score,
            "page_number": table_info["page_number"],
            "category": table_info["category"],
            "match_details": "; ".join(match_details) if match_details else "No specific matches"
        }
    
    def _calculate_page_relevance(self, page_info: Dict[str, Any], query_tokens: List[str]) -> Dict[str, Any]:
        """Calculate relevance score for a page based on multiple criteria."""
        max_score = 0.0
        best_relation = ""
        match_details = []
        
        # Check content relevance (highest weight)
        content_matches = sum(1 for token in query_tokens if token in page_info["content"])
        if content_matches > 0:
            score = min(content_matches / len(query_tokens), 1.0) * 0.7
            if score > max_score:
                max_score = score
                best_relation = "content"
                match_details.append(f"Content matches: {content_matches} tokens")
        
        # Check table titles relevance
        title_matches = sum(1 for token in query_tokens if any(token in title.lower() for title in page_info["table_titles"]))
        if title_matches > 0:
            score = min(title_matches / len(query_tokens), 1.0) * 0.5
            if score > max_score:
                max_score = score
                best_relation = "table_titles"
                match_details.append(f"Table title matches: {title_matches} tokens")
        
        # Check keywords relevance
        keyword_matches = sum(1 for token in query_tokens if token in page_info["keywords"])
        if keyword_matches > 0:
            score = min(keyword_matches / len(query_tokens), 1.0) * 0.3
            if score > max_score:
                max_score = score
                best_relation = "keywords"
                match_details.append(f"Keyword matches: {keyword_matches} tokens")
        
        return {
            "page_title": page_info["page_title"],
            "page_number": page_info["page_number"],
            "relation": best_relation,
            "relevance_score": max_score,
            "match_details": "; ".join(match_details) if match_details else "No specific matches"
        }
    
    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize and normalize search query."""
        # Simple tokenization - split on whitespace and filter
        tokens = re.findall(r'\b\w+\b', query.lower())
        # Filter out very short tokens and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [token for token in tokens if len(token) > 2 and token not in stop_words]
    
    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract keywords from text content."""
        if not text:
            return set()
        
        words = re.findall(r'\b\w+\b', text.lower())
        return {word for word in words if len(word) > 2}
    
    def _extract_page_number(self, page_id: str) -> int:
        """Extract page number from page_id."""
        try:
            return int(page_id.split("_")[-1])
        except (ValueError, IndexError):
            import re
            numbers = re.findall(r'\d+', page_id)
            return int(numbers[0]) if numbers else 0 