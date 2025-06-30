import pytest
from server.engine import etsy_api_engine
from server.engine.etsy_api_engine import EtsyAPI

def test_etsy_api_engine_import():
    assert hasattr(etsy_api_engine, '__file__') 

def test_find_index():
    api = EtsyAPI()
    lst = ['a', 'b', 'c']
    assert api._find_index(lst, 'b') == 1
    assert api._find_index(lst, 'z') == -1 