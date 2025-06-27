import os
import pytest
from src.silo import Silo
from src.toolshed.pitchfork import Pitchfork
from src.models.table import TableInfo, TableRow

def setup_pitchfork():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    silo.load_document('testdoc', data_path)
    pitchfork = Pitchfork(silo)
    pitchfork.build_catalog()
    return pitchfork

def test_build_catalog():
    pitchfork = setup_pitchfork()
    assert pitchfork.is_cataloged

def test_get_table_catalog():
    pitchfork = setup_pitchfork()
    catalog = pitchfork.get_table_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) > 0
    assert hasattr(catalog[0], 'table_id')

def test_get_table_by_id():
    pitchfork = setup_pitchfork()
    catalog = pitchfork.get_table_catalog()
    table_id = catalog[0].table_id
    table = pitchfork.get_table_by_id(table_id)
    assert isinstance(table, dict)
    assert 'table_id' in table 