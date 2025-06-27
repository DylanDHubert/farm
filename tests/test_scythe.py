import os
import pytest
from src.silo import Silo
from src.toolshed.scythe import Scythe
from src.models.search import SemanticSearchResult

def test_scythe_init():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    silo.load_document('testdoc', data_path)
    scythe = Scythe(silo)
    assert scythe.silo is silo

def test_semantic_search_stub():
    silo = Silo()
    data_path = os.path.join('data', 'pb&j_20250626_173624', 'final_output.json')
    silo.load_document('testdoc', data_path)
    scythe = Scythe(silo)
    # This should raise ValueError because embeddings aren't built
    with pytest.raises(ValueError, match="Embeddings not built"):
        scythe.semantic_search('nutrition') 