from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class SearchResult:
    """
    Represents a single search result with metadata.
    """
    page_id: str
    page_title: str
    doc_id: str
    page_number: Optional[int] = None  # For future PDF highlighting
    match_type: str = "keyword"  # "keyword", "title", "table", etc.
    match_score: float = 1.0
    matched_keywords: List[str] = field(default_factory=list)
    context: str = ""  # Brief context of the match
    table_matches: List[Dict[str, Any]] = field(default_factory=list)  # If tables were found

@dataclass
class SemanticSearchResult:
    """Represents a semantic search result with similarity scores."""
    page_id: str
    page_title: str
    doc_id: str
    page_number: Optional[int] = None
    similarity_score: float = 0.0
    semantic_matches: List[str] = field(default_factory=list)
    context: str = ""
    table_matches: List[Dict[str, Any]] = field(default_factory=list)
    embedding_used: str = "" 