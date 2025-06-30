import pytest
from server.engine import etsy_oath_token
from server.engine.etsy_oath_token import generate_code_verifier_and_challenge, write_state, read_state
import tempfile
import os

def test_etsy_oath_token_import():
    assert hasattr(etsy_oath_token, '__file__') 

def test_generate_code_verifier_and_challenge():
    verifier, challenge = generate_code_verifier_and_challenge()
    assert isinstance(verifier, str)
    assert isinstance(challenge, str)
    assert len(verifier) > 0
    assert len(challenge) > 0

def test_read_write_state():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    data = {'foo': 'bar'}
    write_state(data)
    result = read_state()
    assert result.get('foo') == 'bar'
    os.unlink(tmp.name) 