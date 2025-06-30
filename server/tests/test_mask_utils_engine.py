import pytest
from server.engine import mask_utils
from server.engine.mask_utils import convert_react_mask_to_opencv, validate_mask_points
import numpy as np

def test_mask_utils_import():
    assert hasattr(mask_utils, '__file__') 

def test_convert_react_mask_to_opencv():
    points = [{'x': 1, 'y': 1}, {'x': 1, 'y': 5}, {'x': 5, 'y': 5}]
    mask = convert_react_mask_to_opencv(points, (10, 10, 4))
    assert isinstance(mask, np.ndarray)
    assert mask.shape == (10, 10)

def test_validate_mask_points():
    points = [{'x': 1, 'y': 1}, {'x': 1, 'y': 5}, {'x': 5, 'y': 5}]
    assert validate_mask_points(points)
    assert not validate_mask_points([{'x': 1, 'y': 1}]) 