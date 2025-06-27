"""
Silo - Base Data Storage for PB&J Pipeline Outputs

A standalone data container that loads and organizes structured data from multiple
PB&J pipeline outputs. Provides unified access to pages, tables, and metadata
across all loaded documents without any search or retrieval logic.

The Silo is the foundation of the farm architecture, storing all harvested data
in an organized manner for use by other farm tools (Sickle, Pitchfork, Scythe).

Key Features:
- Multi-document support with document isolation
- Unified data access across all loaded documents
- Document metadata tracking and statistics
- Pure data storage (no search/retrieval logic)
- Support for document addition and removal
- Comprehensive statistics and overview capabilities

Example Usage:
    silo = Silo()
    silo.load_document("doc1", "path/to/final_output.json")
    silo.load_document("doc2", "path/to/another_output.json")
    
    # Get all pages from all documents
    all_pages = silo.get_all_pages()
    
    # Get tables from specific document
    doc_tables = silo.get_tables_by_document("doc1")
    
    # Get comprehensive statistics
    stats = silo.get_statistics()
"""

from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class DocumentInfo:
    """
    Information about a loaded document.
    
    Attributes:
        doc_id: Unique identifier for the document
        title: Human-readable title of the document
        loaded_at: Timestamp when the document was loaded
        page_count: Number of pages in the document
        table_count: Number of tables in the document
        keywords: List of keywords extracted from the document
    """
    doc_id: str
    title: str
    loaded_at: datetime
    page_count: int
    table_count: int
    keywords: List[str] = field(default_factory=list)


class Silo:
    """
    Base data storage for PB&J pipeline outputs.
    
    The Silo serves as the foundation of the farm architecture, providing
    organized storage and access to structured document data. It maintains
    document isolation while providing unified access methods.
    
    The Silo does not perform any search or retrieval logic - it focuses
    purely on data organization and access. Search and retrieval capabilities
    are provided by other farm tools (Sickle, Pitchfork, Scythe).
    
    Attributes:
        documents: Dictionary mapping document IDs to their data
        document_info: Dictionary mapping document IDs to DocumentInfo objects
        loaded_at: Dictionary mapping document IDs to load timestamps
    """
    
    def __init__(self):
        """
        Initialize an empty silo.
        
        Creates a new Silo instance with no loaded documents.
        Documents can be added using load_document() or load_documents().
        """
        self.documents: Dict[str, Dict[str, Any]] = {}  # {doc_id: data}
        self.document_info: Dict[str, DocumentInfo] = {}  # {doc_id: info}
        self.loaded_at: Dict[str, datetime] = {}  # {doc_id: loaded_at}
    
    def load_document(self, doc_id: str, data_path: str) -> bool:
        """
        Load a single document from a file path.
        
        Loads a PB&J pipeline final_output.json file and stores it in the silo
        with the specified document ID. Automatically extracts metadata and
        creates a DocumentInfo object for the loaded document.
        
        Args:
            doc_id: Unique identifier for the document (used for disambiguation)
            data_path: Path to the final_output.json file to load
            
        Returns:
            True if document loaded successfully, False if loading failed
            
        Raises:
            FileNotFoundError: If the data file doesn't exist
            json.JSONDecodeError: If the data file contains invalid JSON
            KeyError: If the data file doesn't have expected structure
            
        Example:
            success = silo.load_document("pbj_2024_01", "data/pbj_2024_01/final_output.json")
            if success:
                print("Document loaded successfully")
        """
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
            
            self.documents[doc_id] = data
            self.loaded_at[doc_id] = datetime.now()
            
            # Create document info
            page_count = len(data.get("pages", []))
            table_count = sum(len(page.get("tables", [])) for page in data.get("pages", []))
            keywords = data.get("document_summary", {}).get("combined_keywords", [])
            
            self.document_info[doc_id] = DocumentInfo(
                doc_id=doc_id,
                title=data.get("document_info", {}).get("title", f"Document {doc_id}"),
                loaded_at=self.loaded_at[doc_id],
                page_count=page_count,
                table_count=table_count,
                keywords=keywords
            )
            
            return True
            
        except Exception as e:
            print(f"Error loading document {doc_id}: {e}")
            return False
    
    def load_documents(self, doc_mappings: Dict[str, str]) -> Dict[str, bool]:
        """
        Load multiple documents at once.
        
        Convenience method to load multiple documents in a single call.
        Each document is loaded with its own document ID and file path.
        
        Args:
            doc_mappings: Dictionary mapping document IDs to file paths
                         Format: {doc_id: data_path}
            
        Returns:
            Dictionary mapping document IDs to success status
            Format: {doc_id: success_boolean}
            
        Example:
            mappings = {
                "doc1": "data/doc1/final_output.json",
                "doc2": "data/doc2/final_output.json"
            }
            results = silo.load_documents(mappings)
            # results = {"doc1": True, "doc2": False}
        """
        results = {}
        for doc_id, data_path in doc_mappings.items():
            results[doc_id] = self.load_document(doc_id, data_path)
        return results
    
    def is_loaded(self) -> bool:
        """
        Check if at least one document is loaded.
        
        Returns:
            True if the silo contains at least one document, False otherwise
            
        Example:
            if silo.is_loaded():
                print("Silo has data to work with")
            else:
                print("Silo is empty - load some documents first")
        """
        return bool(self.documents)
    
    def get_document_ids(self) -> List[str]:
        """
        Get list of all loaded document IDs.
        
        Returns:
            List of document IDs for all loaded documents
            
        Example:
            doc_ids = silo.get_document_ids()
            print(f"Loaded documents: {doc_ids}")
        """
        return list(self.documents.keys())
    
    def get_document_info(self, doc_id: Optional[str] = None) -> Union[DocumentInfo, Dict[str, DocumentInfo], None]:
        """
        Get document information.
        
        If a specific doc_id is provided, returns the DocumentInfo for that document.
        If no doc_id is provided, returns a dictionary of all DocumentInfo objects.
        
        Args:
            doc_id: Specific document ID, or None for all documents
            
        Returns:
            DocumentInfo object, dictionary of DocumentInfo objects, or None if doc_id not found
            
        Example:
            # Get info for specific document
            info = silo.get_document_info("doc1")
            if info:
                print(f"Document has {info.page_count} pages")
            
            # Get info for all documents
            all_info = silo.get_document_info()
            for doc_id, info in all_info.items():
                print(f"{doc_id}: {info.page_count} pages, {info.table_count} tables")
        """
        if doc_id:
            return self.document_info.get(doc_id)
        return self.document_info.copy()
    
    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        Get all pages from all documents with document context.
        
        Returns a flat list of all pages from all loaded documents.
        Each page includes a 'doc_id' field to identify its source document.
        
        Returns:
            List of pages with added 'doc_id' field for document disambiguation
            
        Example:
            pages = silo.get_all_pages()
            for page in pages:
                print(f"Page {page['page_id']} from document {page['doc_id']}")
        """
        all_pages = []
        for doc_id, data in self.documents.items():
            for page in data.get("pages", []):
                page_copy = dict(page)
                page_copy["doc_id"] = doc_id
                all_pages.append(page_copy)
        return all_pages
    
    def get_all_tables(self) -> List[Dict[str, Any]]:
        """
        Get all tables from all documents with document context.
        
        Returns a flat list of all tables from all loaded documents.
        Each table includes 'doc_id' and 'page_id' fields for context.
        
        Returns:
            List of tables with added 'doc_id' and 'page_id' fields
            
        Example:
            tables = silo.get_all_tables()
            for table in tables:
                print(f"Table {table['table_id']} from page {table['page_id']} in doc {table['doc_id']}")
        """
        all_tables = []
        for doc_id, data in self.documents.items():
            for page in data.get("pages", []):
                for table in page.get("tables", []):
                    table_copy = dict(table)
                    table_copy["doc_id"] = doc_id
                    table_copy["page_id"] = page["page_id"]
                    all_tables.append(table_copy)
        return all_tables
    
    def get_pages_by_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all pages from a specific document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of pages from the specified document, or empty list if document not found
            
        Example:
            pages = silo.get_pages_by_document("doc1")
            print(f"Document doc1 has {len(pages)} pages")
        """
        data = self.documents.get(doc_id)
        if not data:
            return []
        
        pages = []
        for page in data.get("pages", []):
            page_copy = dict(page)
            page_copy["doc_id"] = doc_id
            pages.append(page_copy)
        return pages
    
    def get_tables_by_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all tables from a specific document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of tables from the specified document, or empty list if document not found
            
        Example:
            tables = silo.get_tables_by_document("doc1")
            print(f"Document doc1 has {len(tables)} tables")
        """
        data = self.documents.get(doc_id)
        if not data:
            return []
        
        tables = []
        for page in data.get("pages", []):
            for table in page.get("tables", []):
                table_copy = dict(table)
                table_copy["doc_id"] = doc_id
                table_copy["page_id"] = page["page_id"]
                tables.append(table_copy)
        return tables
    
    def get_page_by_id(self, page_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific page by ID.
        
        If doc_id is provided, searches only in that document.
        If doc_id is None, searches across all loaded documents.
        
        Args:
            page_id: Page identifier (e.g., "page_1", "page_2")
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Page data with doc_id added, or None if not found
            
        Example:
            # Search in specific document
            page = silo.get_page_by_id("page_1", "doc1")
            
            # Search across all documents
            page = silo.get_page_by_id("page_1")
        """
        docs = [doc_id] if doc_id else self.documents.keys()
        
        for d_id in docs:
            data = self.documents.get(d_id)
            if not data:
                continue
                
            for page in data.get("pages", []):
                if page["page_id"] == page_id:
                    page_copy = dict(page)
                    page_copy["doc_id"] = d_id
                    return page_copy
        
        return None
    
    def get_table_by_id(self, table_id: str, doc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific table by ID.
        
        If doc_id is provided, searches only in that document.
        If doc_id is None, searches across all loaded documents.
        
        Args:
            table_id: Table identifier (e.g., "table_1", "table_2")
            doc_id: Optional document ID for disambiguation
            
        Returns:
            Table data with doc_id and page_id added, or None if not found
            
        Example:
            # Search in specific document
            table = silo.get_table_by_id("table_1", "doc1")
            
            # Search across all documents
            table = silo.get_table_by_id("table_1")
        """
        docs = [doc_id] if doc_id else self.documents.keys()
        
        for d_id in docs:
            data = self.documents.get(d_id)
            if not data:
                continue
                
            for page in data.get("pages", []):
                for table in page.get("tables", []):
                    if table["table_id"] == table_id:
                        table_copy = dict(table)
                        table_copy["doc_id"] = d_id
                        table_copy["page_id"] = page["page_id"]
                        return table_copy
        
        return None
    
    def get_all_keywords(self) -> List[str]:
        """
        Get all unique keywords across all documents.
        
        Returns:
            Sorted list of all unique keywords from all loaded documents
            
        Example:
            keywords = silo.get_all_keywords()
            print(f"Total unique keywords: {len(keywords)}")
        """
        keywords = set()
        for info in self.document_info.values():
            keywords.update(info.keywords)
        return sorted(keywords)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about loaded data.
        
        Returns:
            Dictionary with comprehensive statistics about all loaded data
            
        Example:
            stats = silo.get_statistics()
            print(f"Total documents: {stats['total_documents']}")
            print(f"Total pages: {stats['total_pages']}")
            print(f"Total tables: {stats['total_tables']}")
        """
        total_pages = sum(info.page_count for info in self.document_info.values())
        total_tables = sum(info.table_count for info in self.document_info.values())
        total_keywords = len(self.get_all_keywords())
        
        return {
            "total_documents": len(self.documents),
            "total_pages": total_pages,
            "total_tables": total_tables,
            "total_keywords": total_keywords,
            "documents": {
                doc_id: {
                    "title": info.title,
                    "page_count": info.page_count,
                    "table_count": info.table_count,
                    "keyword_count": len(info.keywords),
                    "loaded_at": info.loaded_at.isoformat()
                }
                for doc_id, info in self.document_info.items()
            }
        }
    
    def clear(self):
        """
        Clear all loaded documents.
        
        Removes all documents from the silo and resets all internal state.
        Use this method to free memory or start fresh.
        
        Example:
            silo.clear()
            print("Silo is now empty")
        """
        self.documents.clear()
        self.document_info.clear()
        self.loaded_at.clear()
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a specific document from the silo.
        
        Args:
            doc_id: Document ID to remove
            
        Returns:
            True if document was removed, False if document didn't exist
            
        Example:
            if silo.remove_document("doc1"):
                print("Document doc1 removed successfully")
            else:
                print("Document doc1 was not found")
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.document_info[doc_id]
            if doc_id in self.loaded_at:
                del self.loaded_at[doc_id]
            return True
        return False 