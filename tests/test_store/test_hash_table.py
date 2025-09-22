import os
from app.core.store.entry import Entry
from app.core.store.segment_manager import SegmentManager
from app.core.store.hash_table import HashTable

import time
import pytest

@pytest.fixture
def setup_tmp_dir(tmp_path):
    yield tmp_path
    # Cleanup after test
    for child in tmp_path.iterdir():
        if child.is_file():
            child.unlink()
    tmp_path.rmdir()
    
def init_segment_manager(base_directory: str) -> SegmentManager:
    return SegmentManager(base_directory, max_segment_size=1024 * 1024 * 10, max_segment_entries=100)

def test_hash_table_recovery_from_segment_manager(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    active_segment = manager.get_active_segment()
    
    entries = [
        Entry(
            timestamp=time.time(),
            key_size=3,
            value_size=5,
            key=b'key1',
            value=b'value1',
            tombstone=False
        ),
        Entry(
            timestamp=time.time(),
            key_size=3,
            value_size=5,
            key=b'key2',
            value=b'value2',
            tombstone=False
        ),
        Entry(
            timestamp=time.time(),
            key_size=3,
            value_size=5,
            key=b'key1',
            value=b'value3',
            tombstone=False
        )
    ]
    
    for entry in entries:
        manager.append(entry)
    
    # Close the active segment to simulate end of writes
    active_segment.close()
    
    # Initialize hash table and recover from segment manager
    hash_table = HashTable()
    hash_table.recover_from_segment_manager(manager)
    
    # Validate hash table contents
    assert hash_table.size() == 2  # key1 and key2
    assert hash_table.get('key1').value_size == 5
    assert hash_table.get('key2').value_size == 5
    assert hash_table.get('key1').timestamp == entries[2].timestamp  # Latest entry for key1
    
def test_hash_table_recovery_with_no_segments(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    hash_table = HashTable()
    hash_table.recover_from_segment_manager(manager)
    assert hash_table.size() == 0
    
def test_hash_table_recovery_with_empty_segment(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    active_segment = manager.get_active_segment()
    active_segment.close()
    
    hash_table = HashTable()
    hash_table.recover_from_segment_manager(manager)
    assert hash_table.size() == 0
    
def test_hash_table_recovery_with_no_index_file(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    active_segment = manager.get_active_segment()
    
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    
    manager.append(entry)
    active_segment.close()
    
    # Remove index file if it exists
    index_file_path = f"{active_segment.filepath}.index"
    if os.path.exists(index_file_path):
        os.remove(index_file_path)
    
    hash_table = HashTable()
    hash_table.recover_from_segment_manager(manager)
    
    assert hash_table.size() == 1
    assert hash_table.get('key').value_size == 5
    assert hash_table.get('key').timestamp == entry.timestamp
    
def test_hash_table_put_and_get():
    hash_table = HashTable()
    
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key1',
        value=b'value1',
        tombstone=False
    )
    
    hash_table.put(key='key1', segment_id=0, offset = 0, size = entry.value_size, timestamp=entry.timestamp)
    retrieved = hash_table.get('key1')
    
    assert retrieved is not None
    assert retrieved.value_size == 5
    assert retrieved.timestamp == entry.timestamp
    
def test_hash_table_delete():
    hash_table = HashTable()
    
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key1',
        value=b'value1',
        tombstone=False
    )
    
    hash_table.put(key='key1',segment_id=0, offset = 0, size = entry.value_size, timestamp=entry.timestamp)
    assert hash_table.size() == 1
    
    hash_table.delete('key1')
    assert hash_table.size() == 0
    assert hash_table.get('key1') is None
    
def test_hash_table_size():
    hash_table = HashTable()
    assert hash_table.size() == 0
    
    entry1 = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key1',
        value=b'value1',
        tombstone=False
    )
    
    entry2 = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key2',
        value=b'value2',
        tombstone=False
    )
    
    hash_table.put(key='key1',segment_id=0, offset = 0, size = entry1.value_size, timestamp=entry1.timestamp)
    assert hash_table.size() == 1
    
    hash_table.put(key='key2',segment_id=0, offset = 0, size = entry2.value_size, timestamp=entry2.timestamp)
    assert hash_table.size() == 2
    
    hash_table.delete('key1')
    assert hash_table.size() == 1
