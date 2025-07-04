# PB&J RAG Toolkit

This document describes the modular tools available for data discovery, exploration, and retrieval in the PB&J RAG system. Tools are organized by phase and type, with consistent naming and clear responsibilities.

---

## Phase 1: Discovery Tools

**Purpose:** Quickly understand what data is available (pages, tables, keywords).

### Page Discovery
- **Class:** `PageDiscovery`
- **Function:** `view_pages()`
- **Returns:** List of all pages with number, title, and doc_id.
- **Example:**
    ```python
    pages = PageDiscovery(silo).view_pages()
    # [{"page_number": 1, "page_title": "Intro", "doc_id": "..."}, ...]
    ```

### Keyword Discovery
- **Class:** `KeywordDiscovery`
- **Function:** `view_keywords()`
- **Returns:** List of all unique keywords in the dataset.
- **Example:**
    ```python
    keywords = KeywordDiscovery(silo).view_keywords()
    # ["acetabular", "protocol", ...]
    ```

### Table Discovery
- **Class:** `TableDiscovery`
- **Function:** `view_tables()`
- **Returns:** List of all tables with title, category, page number, and metadata.
- **Example:**
    ```python
    tables = TableDiscovery(silo).view_tables()
    # [{"table_title": "Nutrition Info", "category": "data", ...}, ...]
    ```

---

## Phase 2: Exploration Tools

**Purpose:** Find and summarize relevant data for a query.

### Table Explorer
- **Class:** `TableExplorer`
- **Function:** `table_summary(table_name)`
- **Parameters:**
    - `table_name` (str): Title of the table
- **Returns:** Table metadata, columns, sample data
- **Example:**
    ```python
    summary = TableExplorer(silo).table_summary("Nutrition Info")
    # {"table_title": ..., "columns": [...], ...}
    ```

### Relevance Finder
- **Class:** `RelevanceFinder`
- **Functions:**
    - `find_relevant_tables(search_query)`
    - `find_relevant_pages(search_query)`
- **Parameters:**
    - `search_query` (str): Query string
- **Returns:** List of relevant tables/pages with relation and score
- **Example:**
    ```python
    tables = RelevanceFinder(silo).find_relevant_tables("surgical protocol")
    # [{"table_name": ..., "relation": ..., "relevance_score": ...}, ...]
    pages = RelevanceFinder(silo).find_relevant_pages("surgical protocol")
    # [{"page_title": ..., "relation": ..., "relevance_score": ...}, ...]
    ```

---

## Phase 3: Retrieval Tools

**Purpose:** Retrieve specific data for analysis or answer generation.

### Table Retriever
- **Class:** `TableRetriever`
- **Function:** `get_table_data(table_name, columns="all")`
- **Parameters:**
    - `table_name` (str): Title of the table
    - `columns` (str or list): "all" or list of column names
- **Returns:** Table data (rows, columns, metadata)
- **Example:**
    ```python
    data = TableRetriever(silo).get_table_data("Nutrition Info", columns=["Calories", "Fat"])
    # {"columns": ["Calories", "Fat"], "rows": [...], ...}
    ```

### Row Retriever
- **Class:** `RowRetriever`
- **Functions:**
    - `get_row_data(table_name, column, target)`
    - `get_rows_by_multiple_criteria(table_name, criteria)`
- **Parameters:**
    - `table_name` (str): Title of the table
    - `column` (str): Column name
    - `target` (str): Value to match
    - `criteria` (dict): {column: value, ...}
- **Returns:** Matching rows
- **Example:**
    ```python
    rows = RowRetriever(silo).get_row_data("Nutrition Info", "Calories", "100")
    # {"matching_rows": [...], ...}
    rows = RowRetriever(silo).get_rows_by_multiple_criteria("Nutrition Info", {"Calories": "100", "Fat": "0"})
    # {"matching_rows": [...], ...}
    ```

### Page Retriever
- **Class:** `PageRetriever`
- **Function:** `get_page_content(page_identifier)`
- **Parameters:**
    - `page_identifier` (str or int): Page title or number
- **Returns:** Page content, tables, metadata
- **Example:**
    ```python
    page = PageRetriever(silo).get_page_content(1)
    # {"page_title": ..., "content": ..., ...}
    page = PageRetriever(silo).get_page_content("Intro")
    # {"page_title": ..., "content": ..., ...}
    ```

---

## Usage Pattern

1. **Discovery:** Use `view_pages`, `view_keywords`, `view_tables` to get a sense of the data.
2. **Exploration:** Use `table_summary` and `find_relevant_tables/pages` to narrow down relevant data.
3. **Retrieval:** Use `get_table_data`, `get_row_data`, and `get_page_content` to extract the specific information you need.

---

## Notes
- All tools require a loaded `Silo` instance.
- All functions raise `ValueError` if data is not loaded or parameters are invalid.
- All return types are Python dictionaries/lists for easy downstream use.

---

For more details, see the code in `src/toolshed/` or ask for specific usage examples. 