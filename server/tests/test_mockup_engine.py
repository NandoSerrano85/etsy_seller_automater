import pytest
from server.engine import mockup_engine
import numpy as np
import cv2
import tempfile
from server.engine.mockup_engine import MockupTemplateCache

def test_mockup_engine_import():
    assert hasattr(mockup_engine, '__file__') 

def test_get_mockup():
    img = np.ones((10, 10, 4), dtype=np.uint8) * 255
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(tmp.name, img)
    cache = MockupTemplateCache()
    result = cache.get_mockup(tmp.name)
    assert result.shape == (10, 10, 4) 