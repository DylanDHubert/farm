from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class TableInfo:
    """Information about a table with document context."""
    table_id: str
    title: str
    description: str
    doc_id: str
    page_id: str
    page_number: Optional[int] = None
    row_count: int = 0
    column_count: int = 0
    technical_category: str = ""
    data_types: List[str] = field(default_factory=list)

@dataclass
class TableRow:
    """Represents a single table row with metadata."""
    row_index: int
    data: Dict[str, Any]
    table_id: str
    doc_id: str
    page_id: str 