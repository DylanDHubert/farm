import os
import pytest
from src.barn import Barn

def setup_barn():
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    barn = Barn(data_path)
    return barn

def test_query():
    barn = setup_barn()
    response = barn.query('peanut butter')
    assert hasattr(response, 'answer')
    assert hasattr(response, 'context')
    assert hasattr(response, 'sources')

def test_get_data_overview():
    barn = setup_barn()
    overview = barn.get_data_overview()
    assert isinstance(overview, dict)
    assert 'statistics' in overview
    assert 'total_documents' in overview['statistics']

def test_get_available_documents():
    barn = setup_barn()
    docs = barn.get_available_documents()
    assert isinstance(docs, list)
    assert len(docs) > 0 