import pytest
import os
import numpy as np
import cv2
from server.engine import cropping
import tempfile
from server.engine.cropping import crop_transparent

def test_cropping_import():
    assert hasattr(cropping, '__file__') 

def test_crop_transparent_alpha():
    # Create a dummy RGBA image with a transparent border
    img = np.zeros((10, 10, 4), dtype=np.uint8)
    img[2:8, 2:8, :] = 255  # Opaque square in the center
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(tmp.name, img)
    cropped = crop_transparent(tmp.name)
    os.unlink(tmp.name)
    assert cropped.shape[0] == 6 and cropped.shape[1] == 6 