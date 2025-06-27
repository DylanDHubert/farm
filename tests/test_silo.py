import os
import pytest
from src.silo import Silo

def test_load_document():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    assert silo.load_document('testdoc', data_path) is True
    assert 'testdoc' in silo.documents
    assert silo.is_loaded()

def test_get_all_pages():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    silo.load_document('testdoc', data_path)
    pages = silo.get_all_pages()
    assert isinstance(pages, list)
    assert len(pages) > 0
    assert 'page_id' in pages[0]

def test_get_all_tables():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    silo.load_document('testdoc', data_path)
    tables = silo.get_all_tables()
    assert isinstance(tables, list)
    assert len(tables) > 0
    assert 'table_id' in tables[0] 