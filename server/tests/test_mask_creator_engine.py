import pytest
from server.engine import mask_creator_engine
import numpy as np
import cv2
import tempfile
from server.engine.mask_creator_engine import MaskCreator

def test_mask_creator_engine_import():
    assert hasattr(mask_creator_engine, '__file__') 

def test_mask_creator_instantiation():
    creator = MaskCreator(["dummy.png"])
    assert isinstance(creator, MaskCreator)

# Optionally test resize_for_display if it doesn't require GUI 