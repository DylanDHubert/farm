"""
Sickle - Fast Keyword Search for PB&J Data

A precise, efficient keyword search tool that cuts through data like a sickle
through wheat. Provides fast keyword-based search across pages, tables, and
metadata with support for page-level results and future PDF highlighting.

The Sickle is designed for speed and precision, using inverted indexes to
provide fast keyword matching across large datasets. It supports multiple
search types and provides rich context in search results.

Key Features:
- Fast keyword indexing with inverted index
- Multiple search types (all, pages, tables, titles)
- Page number support for PDF highlighting
- Keyword-based scoring and ranking
- Context-aware results with table matches
- Support for both natural language and keyword list queries
- Document disambiguation in results

Example Usage:
    from sickle import Sickle
    from silo import Silo
    
    silo = Silo()
    silo.load_document("doc1", "path/to/data.json")
    
    sickle = Sickle(silo)
    sickle.build_index()
    
    # Search for content
    results = sickle.search("compatibility", search_type="all", limit=5)
    
    # Search by specific keywords
    results = sickle.search_by_keywords(["jelly", "jam"], search_type="tables")
    
    # Get page by number for PDF highlighting
    page = sickle.get_page_by_number(1)
"""

from typing import Dict, List, Optional, Any, Set
import re
from collections import defaultdict
from silo import Silo
from models.search import SearchResult


class Sickle:
    """
    Fast keyword search tool for PB&J data.
    
    The Sickle provides efficient keyword-based search capabilities using
    inverted indexes for fast lookups. It indexes pages, tables, and metadata
    to enable quick retrieval of relevant content.
    
    The Sickle is designed to work with Silo data and provides rich search
    results with context and scoring. It supports multiple search types and
    can be used for both simple keyword matching and complex queries.
    
    Attributes:
        silo: Silo instance containing the data to search
        index: Main search index (internal use)
        page_index: Page-level metadata index
        table_index: Table-level metadata index
        keyword_index: Inverted index mapping keywords to page IDs
        is_indexed: Whether the search index has been built
    """
    
    def __init__(self, silo: Silo):
        """
        Initialize the sickle with a silo of data.
        
        Creates a new Sickle instance that will search through the provided
        Silo data. The search index must be built before searching.
        
        Args:
            silo: Silo instance containing the data to search
            
        Example:
            silo = Silo()
            silo.load_document("doc1", "path/to/data.json")
            sickle = Sickle(silo)
            sickle.build_index()
        """
        self.silo = silo
        self.index = {}  # Main search index
        self.page_index = {}  # Page-level metadata
        self.table_index = {}  # Table-level metadata
        self.keyword_index = defaultdict(set)  # Keyword -> page_ids mapping
        self.is_indexed = False
    
    def build_index(self):
        """
        Build search index from silo data.
        
        Creates an inverted index of all keywords from pages, tables, and
        metadata. This method must be called before any search operations.
        The index is optimized for fast keyword lookups.
        
        Raises:
            ValueError: If no data is available in the silo
            
        Example:
            sickle.build_index()
            print("Search index built successfully")
        """
        if not self.silo.is_loaded():
            raise ValueError("No data available in silo for indexing")
        
        # Clear existing index
        self.index.clear()
        self.page_index.clear()
        self.table_index.clear()
        self.keyword_index.clear()
        
        # Get all pages from silo
        pages = self.silo.get_all_pages()
        
        for page in pages:
            page_id = page["page_id"]
            doc_id = page["doc_id"]
            
            # Extract page number from page_id (e.g., "page_1" -> 1)
            page_number = self._extract_page_number(page_id)
            
            # Index page-level content
            self._index_page(page, page_number)
            
            # Index tables within the page
            for table in page["tables"]:
                self._index_table(table, page_id, doc_id, page_number)
        
        self.is_indexed = True
    
    def search(self, query: str, search_type: str = "all", limit: int = 10) -> List[SearchResult]:
        """
        Search for pages matching the query.
        
        Performs keyword-based search using natural language queries.
        The query is tokenized and normalized before searching.
        
        Args:
            query: Search query string (natural language)
            search_type: Type of search ("all", "pages", "tables", "titles")
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects, sorted by relevance score
            
        Raises:
            ValueError: If index not built or invalid search_type
            
        Example:
            # Search across all content
            results = sickle.search("peanut butter compatibility", search_type="all", limit=5)
            
            # Search only in titles
            results = sickle.search("bread", search_type="titles", limit=3)
            
            # Search only in tables
            results = sickle.search("nutrition", search_type="tables", limit=5)
        """
        if not self.is_indexed:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Normalize and tokenize query
        query_tokens = self._tokenize_query(query)
        
        if not query_tokens:
            return []
        
        # Search based on type
        if search_type == "all":
            results = self._search_all(query_tokens)
        elif search_type == "pages":
            results = self._search_pages(query_tokens)
        elif search_type == "tables":
            results = self._search_tables(query_tokens)
        elif search_type == "titles":
            results = self._search_titles(query_tokens)
        else:
            raise ValueError(f"Unknown search_type: {search_type}")
        
        # Sort by score and limit results
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results[:limit]
    
    def search_by_keywords(self, keywords: List[str], search_type: str = "all", limit: int = 10) -> List[SearchResult]:
        """
        Search using a list of specific keywords.
        
        Performs keyword-based search using a predefined list of keywords.
        This method is useful when you have specific terms to search for
        rather than natural language queries.
        
        Args:
            keywords: List of keywords to search for
            search_type: Type of search ("all", "pages", "tables", "titles")
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects, sorted by relevance score
            
        Raises:
            ValueError: If index not built or invalid search_type
            
        Example:
            # Search for specific ingredients
            results = sickle.search_by_keywords(["jelly", "jam", "preserves"], search_type="all")
            
            # Search for technical terms
            results = sickle.search_by_keywords(["compatibility", "measurement"], search_type="tables")
        """
        if not self.is_indexed:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Normalize keywords
        normalized_keywords = [self._normalize_keyword(kw) for kw in keywords if kw.strip()]
        
        if not normalized_keywords:
            return []
        
        # Search based on type
        if search_type == "all":
            results = self._search_all(normalized_keywords)
        elif search_type == "pages":
            results = self._search_pages(normalized_keywords)
        elif search_type == "tables":
            results = self._search_tables(normalized_keywords)
        elif search_type == "titles":
            results = self._search_titles(normalized_keywords)
        else:
            raise ValueError(f"Unknown search_type: {search_type}")
        
        # Sort by score and limit results
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results[:limit]
    
    def get_page_by_number(self, page_number: int, doc_id: Optional[str] = None) -> Optional[SearchResult]:
        """
        Get page by page number (for PDF highlighting).
        
        Retrieves a specific page by its page number. This is useful for
        PDF highlighting and navigation where you need to map search results
        to specific page numbers.
        
        Args:
            page_number: Page number to retrieve (1-based)
            doc_id: Optional document ID for disambiguation
            
        Returns:
            SearchResult for the page, or None if not found
            
        Example:
            # Get page 1 from any document
            page = sickle.get_page_by_number(1)
            
            # Get page 1 from specific document
            page = sickle.get_page_by_number(1, "doc1")
        """
        docs = [doc_id] if doc_id else self.silo.get_document_ids()
        
        for d_id in docs:
            for page_id, page_data in self.page_index.items():
                if (page_data.get("page_number") == page_number and 
                    page_data.get("doc_id") == d_id):
                    return SearchResult(
                        page_id=page_id,
                        page_title=page_data["title"],
                        doc_id=d_id,
                        page_number=page_number,
                        match_type="page_number",
                        match_score=1.0,
                        matched_keywords=[],
                        context=f"Page {page_number}"
                    )
        return None
    
    def get_available_keywords(self) -> List[str]:
        """
        Get all available keywords in the index.
        
        Returns a sorted list of all keywords that have been indexed.
        This is useful for understanding what terms are available for search
        and for building autocomplete functionality.
        
        Returns:
            List of all indexed keywords, sorted alphabetically
            
        Example:
            keywords = sickle.get_available_keywords()
            print(f"Available keywords: {keywords[:10]}...")
        """
        return sorted(list(self.keyword_index.keys()))
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search index.
        
        Returns comprehensive statistics about the search index, including
        the number of indexed pages, tables, and keywords.
        
        Returns:
            Dictionary with index statistics
            
        Example:
            stats = sickle.get_index_stats()
            print(f"Indexed {stats['total_pages']} pages and {stats['total_tables']} tables")
        """
        return {
            "total_pages": len(self.page_index),
            "total_tables": len(self.table_index),
            "total_keywords": len(self.keyword_index),
            "is_indexed": self.is_indexed
        }
    
    # ==================== PRIVATE METHODS ====================
    
    def _extract_page_number(self, page_id: str) -> Optional[int]:
        """
        Extract page number from page_id.
        
        Extracts the numeric page number from page IDs like "page_1", "page_2", etc.
        
        Args:
            page_id: Page identifier string
            
        Returns:
            Page number as integer, or None if not found
        """
        match = re.search(r'page_(\d+)', page_id)
        return int(match.group(1)) if match else None
    
    def _normalize_keyword(self, keyword: str) -> str:
        """
        Normalize keyword for indexing and searching.
        
        Converts keyword to lowercase and strips whitespace for consistent
        indexing and matching.
        
        Args:
            keyword: Raw keyword string
            
        Returns:
            Normalized keyword string
        """
        return keyword.lower().strip()
    
    def _tokenize_query(self, query: str) -> List[str]:
        """
        Tokenize and normalize search query.
        
        Splits a natural language query into individual tokens, normalizes
        them, and filters out very short tokens.
        
        Args:
            query: Natural language query string
            
        Returns:
            List of normalized tokens
        """
        # Simple tokenization - split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', query.lower())
        return [token for token in tokens if len(token) > 2]  # Filter out very short tokens
    
    def _index_page(self, page: Dict[str, Any], page_number: Optional[int]):
        """
        Index a single page.
        
        Creates search index entries for a single page, including its title,
        keywords, and summary.
        
        Args:
            page: Page data dictionary
            page_number: Extracted page number
        """
        page_id = page["page_id"]
        doc_id = page["doc_id"]
        
        # Store page metadata
        self.page_index[page_id] = {
            "title": page["title"],
            "summary": page["summary"],
            "keywords": page["keywords"],
            "page_number": page_number,
            "doc_id": doc_id,
            "table_count": len(page["tables"])
        }
        
        # Index page title
        title_tokens = self._tokenize_query(page["title"])
        for token in title_tokens:
            self.keyword_index[token].add(page_id)
        
        # Index page keywords
        for keyword in page["keywords"]:
            normalized = self._normalize_keyword(keyword)
            self.keyword_index[normalized].add(page_id)
        
        # Index page summary (optional - for more comprehensive search)
        summary_tokens = self._tokenize_query(page["summary"])
        for token in summary_tokens:
            self.keyword_index[token].add(page_id)
    
    def _index_table(self, table: Dict[str, Any], page_id: str, doc_id: str, page_number: Optional[int]):
        """
        Index a single table.
        
        Creates search index entries for a single table, including its title,
        description, and technical category.
        
        Args:
            table: Table data dictionary
            page_id: ID of the page containing the table
            doc_id: ID of the document containing the table
            page_number: Page number for context
        """
        table_id = table["table_id"]
        
        # Store table metadata
        self.table_index[table_id] = {
            "title": table["title"],
            "description": table["description"],
            "page_id": page_id,
            "doc_id": doc_id,
            "page_number": page_number,
            "row_count": table["metadata"]["row_count"],
            "technical_category": table["metadata"]["technical_category"]
        }
        
        # Index table title
        title_tokens = self._tokenize_query(table["title"])
        for token in title_tokens:
            self.keyword_index[token].add(page_id)
        
        # Index table description
        desc_tokens = self._tokenize_query(table["description"])
        for token in desc_tokens:
            self.keyword_index[token].add(page_id)
        
        # Index technical category
        category_tokens = self._tokenize_query(table["metadata"]["technical_category"])
        for token in category_tokens:
            self.keyword_index[token].add(page_id)
    
    def _search_all(self, tokens: List[str]) -> List[SearchResult]:
        """
        Search across all content types.
        
        Performs comprehensive search across pages, tables, and metadata.
        Returns results with the highest relevance scores.
        
        Args:
            tokens: List of normalized search tokens
            
        Returns:
            List of SearchResult objects
        """
        results = []
        page_matches: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"score": 0, "keywords": set(), "tables": []})
        
        for token in tokens:
            matching_pages = self.keyword_index.get(token, set())
            
            for page_id in matching_pages:
                page_data = self.page_index[page_id]
                page_matches[page_id]["score"] += 1
                page_matches[page_id]["keywords"].add(token)
                
                # Check for table matches
                for table_id, table_data in self.table_index.items():
                    if table_data["page_id"] == page_id:
                        if token in self._tokenize_query(table_data["title"]) or \
                           token in self._tokenize_query(table_data["description"]) or \
                           token in self._tokenize_query(table_data["technical_category"]):
                            page_matches[page_id]["tables"].append(table_data)
        
        # Convert to SearchResult objects
        for page_id, match_data in page_matches.items():
            page_data = self.page_index[page_id]
            
            # Create meaningful context
            context_parts = []
            if page_data["title"]:
                context_parts.append(f"Page: {page_data['title']}")
            if page_data["summary"]:
                context_parts.append(f"Summary: {page_data['summary'][:200]}...")
            if match_data["keywords"]:
                context_parts.append(f"Matched keywords: {', '.join(match_data['keywords'])}")
            if match_data["tables"]:
                table_names = [table["title"] for table in match_data["tables"]]
                context_parts.append(f"Relevant tables: {', '.join(table_names)}")
            
            context = " | ".join(context_parts)
            
            results.append(SearchResult(
                page_id=page_id,
                page_title=page_data["title"],
                doc_id=page_data["doc_id"],
                page_number=page_data["page_number"],
                match_type="all",
                match_score=float(match_data["score"]),
                matched_keywords=list(match_data["keywords"]),
                context=context,
                table_matches=match_data["tables"]
            ))
        
        return results
    
    def _search_pages(self, tokens: List[str]) -> List[SearchResult]:
        """
        Search only page-level content.
        
        Performs search only on page titles, keywords, and summaries.
        Excludes table content from the search.
        
        Args:
            tokens: List of normalized search tokens
            
        Returns:
            List of SearchResult objects
        """
        results = []
        page_matches: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"score": 0, "keywords": set()})
        
        for token in tokens:
            matching_pages = self.keyword_index.get(token, set())
            
            for page_id in matching_pages:
                page_data = self.page_index[page_id]
                page_matches[page_id]["score"] += 1
                page_matches[page_id]["keywords"].add(token)
        
        # Convert to SearchResult objects
        for page_id, match_data in page_matches.items():
            page_data = self.page_index[page_id]
            
            # Create meaningful context
            context_parts = []
            if page_data["title"]:
                context_parts.append(f"Page: {page_data['title']}")
            if page_data["summary"]:
                context_parts.append(f"Summary: {page_data['summary'][:200]}...")
            if match_data["keywords"]:
                context_parts.append(f"Matched keywords: {', '.join(match_data['keywords'])}")
            
            context = " | ".join(context_parts)
            
            results.append(SearchResult(
                page_id=page_id,
                page_title=page_data["title"],
                doc_id=page_data["doc_id"],
                page_number=page_data["page_number"],
                match_type="pages",
                match_score=float(match_data["score"]),
                matched_keywords=list(match_data["keywords"]),
                context=context
            ))
        
        return results
    
    def _search_tables(self, tokens: List[str]) -> List[SearchResult]:
        """
        Search only table content.
        
        Performs search only on table titles, descriptions, and technical categories.
        Returns pages that contain matching tables.
        
        Args:
            tokens: List of normalized search tokens
            
        Returns:
            List of SearchResult objects
        """
        results = []
        page_matches: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"score": 0, "keywords": set(), "tables": []})
        
        for token in tokens:
            for table_id, table_data in self.table_index.items():
                if token in self._tokenize_query(table_data["title"]) or \
                   token in self._tokenize_query(table_data["description"]) or \
                   token in self._tokenize_query(table_data["technical_category"]):
                    
                    page_id = table_data["page_id"]
                    page_matches[page_id]["score"] += 1
                    page_matches[page_id]["keywords"].add(token)
                    page_matches[page_id]["tables"].append(table_data)
        
        # Convert to SearchResult objects
        for page_id, match_data in page_matches.items():
            page_data = self.page_index[page_id]
            
            # Create meaningful context
            context_parts = []
            if page_data["title"]:
                context_parts.append(f"Page: {page_data['title']}")
            if match_data["tables"]:
                table_names = [table["title"] for table in match_data["tables"]]
                context_parts.append(f"Relevant tables: {', '.join(table_names)}")
            if match_data["keywords"]:
                context_parts.append(f"Matched keywords: {', '.join(match_data['keywords'])}")
            
            context = " | ".join(context_parts)
            
            results.append(SearchResult(
                page_id=page_id,
                page_title=page_data["title"],
                doc_id=page_data["doc_id"],
                page_number=page_data["page_number"],
                match_type="tables",
                match_score=float(match_data["score"]),
                matched_keywords=list(match_data["keywords"]),
                context=context,
                table_matches=match_data["tables"]
            ))
        
        return results
    
    def _search_titles(self, tokens: List[str]) -> List[SearchResult]:
        """
        Search only titles (page and table titles).
        
        Performs search only on page and table titles.
        Useful for finding content with specific naming patterns.
        
        Args:
            tokens: List of normalized search tokens
            
        Returns:
            List of SearchResult objects
        """
        results = []
        page_matches: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"score": 0, "keywords": set()})
        
        for token in tokens:
            # Search page titles
            for page_id, page_data in self.page_index.items():
                if token in self._tokenize_query(page_data["title"]):
                    page_matches[page_id]["score"] += 1
                    page_matches[page_id]["keywords"].add(token)
            
            # Search table titles
            for table_id, table_data in self.table_index.items():
                if token in self._tokenize_query(table_data["title"]):
                    page_id = table_data["page_id"]
                    page_matches[page_id]["score"] += 1
                    page_matches[page_id]["keywords"].add(token)
        
        # Convert to SearchResult objects
        for page_id, match_data in page_matches.items():
            page_data = self.page_index[page_id]
            
            # Create meaningful context
            context_parts = []
            if page_data["title"]:
                context_parts.append(f"Page: {page_data['title']}")
            if match_data["keywords"]:
                context_parts.append(f"Matched keywords: {', '.join(match_data['keywords'])}")
            
            context = " | ".join(context_parts)
            
            results.append(SearchResult(
                page_id=page_id,
                page_title=page_data["title"],
                doc_id=page_data["doc_id"],
                page_number=page_data["page_number"],
                match_type="titles",
                match_score=float(match_data["score"]),
                matched_keywords=list(match_data["keywords"]),
                context=context
            ))
        
        return results 