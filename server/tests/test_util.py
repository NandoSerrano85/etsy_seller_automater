import pytest
from server.engine import util
import numpy as np
from server.engine.util import inches_to_pixels, rotate_image_90

def test_util_import():
    assert hasattr(util, '__file__') 

def test_inches_to_pixels():
    assert inches_to_pixels(2, 400) == 800

def test_rotate_image_90():
    img = np.ones((10, 10, 3), dtype=np.uint8)
    rotated = rotate_image_90(img)
    assert rotated.shape == (10, 10, 3) 