import os
from app.core import BitcaskStore

import pytest

@pytest.fixture
def setup_tmp_dir(tmp_path):
    yield tmp_path
    # Cleanup after test
    for child in tmp_path.iterdir():
        if child.is_file():
            child.unlink()
    tmp_path.rmdir()
    
def test_bitcask_store_put_get(setup_tmp_dir):
    store = BitcaskStore(str(setup_tmp_dir))
    store.put('key1', 'value1')
    store.put('key2', 'value2')
    
    assert store.get('key1') == 'value1'
    assert store.get('key2') == 'value2'
    
def test_bitcask_store_delete(setup_tmp_dir):
    store = BitcaskStore(str(setup_tmp_dir))
    store.put('key1', 'value1')
    assert store.get('key1') == 'value1'
    
    store.delete('key1')
    assert store.get('key1') is None
        
def test_bitcask_store_recovery(setup_tmp_dir):
    store = BitcaskStore(str(setup_tmp_dir))
    store.put('key1', 'value1')
    store.put('key2', 'value2')
    
    assert store.get('key1') == 'value1'
    assert store.get('key2') == 'value2'
    
    # Simulate restart by creating a new instance
    store = BitcaskStore(str(setup_tmp_dir))
    
    assert store.get('key1') == 'value1'
    assert store.get('key2') == 'value2'
    
    store.delete('key1')
    assert store.get('key1') is None
        
def test_bitcask_store_overwrite(setup_tmp_dir):
    store = BitcaskStore(str(setup_tmp_dir))
    store.put('key1', 'value1')
    assert store.get('key1') == 'value1'
    
    store.put('key1', 'value2')
    assert store.get('key1') == 'value2'
    
def test_bitcask_store_nonexistent_key(setup_tmp_dir):
    store = BitcaskStore(str(setup_tmp_dir))
    value = store.get('nonexistent_key')
    assert value is None
        
def test_bitcask_store_large_value(setup_tmp_dir):
    store = BitcaskStore(str(setup_tmp_dir))
    large_value = 'v' * 10**6  # 1 MB value
    store.put('large_key', large_value)
    assert store.get('large_key') == large_value

    