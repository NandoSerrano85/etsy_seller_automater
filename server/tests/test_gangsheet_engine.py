import pytest
from server.engine import gangsheet_engine
import numpy as np
import cv2
import tempfile
from server.engine.gangsheet_engine import process_image

def test_gangsheet_engine_import():
    assert hasattr(gangsheet_engine, '__file__') 

def test_process_image_valid():
    img = np.ones((10, 10, 4), dtype=np.uint8) * 255
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(tmp.name, img)
    result = process_image(tmp.name)
    assert result is not None

def test_process_image_invalid():
    result = process_image('nonexistent.png')
    assert result is None 