import os
import pytest
from src.silo import Silo
from src.toolshed.sickle import Sickle
from src.models.search import SearchResult

def setup_sickle():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    silo.load_document('testdoc', data_path)
    sickle = Sickle(silo)
    sickle.build_index()
    return sickle

def test_build_index():
    sickle = setup_sickle()
    assert sickle.is_indexed

def test_search_keyword():
    sickle = setup_sickle()
    results = sickle.search('peanut', search_type='all', limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    assert hasattr(results[0], 'page_id')

def test_get_available_keywords():
    sickle = setup_sickle()
    keywords = sickle.get_available_keywords()
    assert isinstance(keywords, list)
    assert 'peanut' in [k.lower() for k in keywords] 