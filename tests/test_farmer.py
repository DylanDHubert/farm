import os
import pytest
from src.farmer import Farmer

def setup_farmer():
    farmer = Farmer()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    farmer.load_document('testdoc', data_path)
    return farmer

def test_load_document():
    farmer = setup_farmer()
    assert farmer.is_ready()
    assert 'testdoc' in farmer.silo.documents

def test_search():
    farmer = setup_farmer()
    results = farmer.search('peanut', search_type='all', limit=5)
    assert isinstance(results, list)
    assert len(results) > 0

def test_get_table_catalog():
    farmer = setup_farmer()
    catalog = farmer.get_table_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) > 0 