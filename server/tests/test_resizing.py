import pytest
from server.engine import resizing
import numpy as np
import cv2
import tempfile
from server.engine.resizing import resize_image_by_inches
from server.engine.util import inches_to_pixels

def test_resizing_import():
    assert hasattr(resizing, '__file__') 

def test_inches_to_pixels():
    assert inches_to_pixels(2, 400) == 800

def test_resize_image_by_inches():
    img = np.ones((10, 10, 4), dtype=np.uint8) * 255
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(tmp.name, img)
    result = resize_image_by_inches(tmp.name, 'UVDTF 16oz')
    assert result is not None 