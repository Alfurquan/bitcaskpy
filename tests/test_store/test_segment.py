from core.bitcaskpy.store.segment import Segment
from core.bitcaskpy.store.entry import Entry

import time
import os
import pytest

@pytest.fixture
def setup_tmp_dir(tmp_path):
    yield tmp_path
    # Cleanup after test
    for child in tmp_path.iterdir():
        if child.is_file():
            child.unlink()
    tmp_path.rmdir()

def test_segment_new(setup_tmp_dir):
    segment = Segment.new_segment(1, str(setup_tmp_dir), 1024, 100)
    assert segment.id == 1
    assert segment.filepath == f"{setup_tmp_dir}/segment_1.log"
    assert segment.metadata_filepath == f"{setup_tmp_dir}/segment_1.hint"
    assert segment.size == 0
    assert segment.num_entries == 0
    assert segment.active is True
    assert segment.max_size == 1024
    assert segment.max_entries == 100
    assert segment.closed is False
    
    assert os.path.exists(segment.filepath)
    assert os.path.getsize(segment.filepath) == 0
    assert os.path.exists(segment.metadata_filepath)
    assert os.path.getsize(segment.metadata_filepath) != 0

def test_segment_close(setup_tmp_dir):
    segment = Segment.new_segment(1, str(setup_tmp_dir), 1024, 100)
    last_sync = segment.last_sync
    
    segment.close()
    
    assert segment.closed is True
    assert segment.active is False
    
    # ensure metadata is synced to disk
    assert os.path.exists(segment.metadata_filepath)
    assert os.path.getsize(segment.metadata_filepath) != 0
    assert segment.last_sync > last_sync
    
    
def test_segment_is_active(setup_tmp_dir):
    segment = Segment.new_segment(1, str(setup_tmp_dir), 1024, 100)
    assert segment.is_active() is True
    segment.close()
    assert segment.is_active() is False
    
def test_segment_append_and_read(tmp_path):
    segment = Segment.new_segment(1, str(tmp_path), 1024, 100)
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    
    segment.append(entry)
    
    read_entry = segment.read(0)
    assert read_entry == entry
    
def test_segment_append_exceeds_size(setup_tmp_dir):
    segment = Segment.new_segment(1, str(setup_tmp_dir), 50, 100)
    entry = Entry(
        timestamp=time.time(),
        key_size=30,
        value_size=25,
        key=b'k'*30,
        value=b'v'*25,
        tombstone=False
    )
    
    with pytest.raises(ValueError, match="Segment is full"):
        segment.append(entry)

def test_segment_append_exceeds_entries(setup_tmp_dir):
    segment = Segment.new_segment(1, str(setup_tmp_dir), 1024, 2)
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    
    segment.append(entry)
    segment.append(entry)
    
    with pytest.raises(ValueError, match="Segment is full"):
        segment.append(entry)
        
def test_open_segment_after_close(setup_tmp_dir):
    segment = Segment.new_segment(1, str(setup_tmp_dir), 1024, 100)
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    
    segment.append(entry)
    segment.append(entry)
    
    segment.close()
    
    reopened = Segment.open_segment(1, str(setup_tmp_dir))
    assert reopened.id == segment.id
    assert reopened.filepath == segment.filepath
    assert reopened.metadata_filepath == segment.metadata_filepath
    assert reopened.size == segment.size
    assert reopened.num_entries == segment.num_entries
    assert reopened.active is False
    assert reopened.closed is True
    assert reopened.max_size == segment.max_size
    assert reopened.max_entries == segment.max_entries
    
    read_entry = reopened.read(0)
    assert read_entry == entry
    
def test_open_segment_missing_metadata(setup_tmp_dir):
    # Create segment, delete hint file, test recovery
    segment = Segment.new_segment(1, str(setup_tmp_dir))
    os.remove(segment.metadata_filepath)
    
    recovered = Segment.open_segment(1, str(setup_tmp_dir))
    assert recovered.closed is True 
    assert recovered.active is False
    assert recovered.num_entries == 0
    assert recovered.size == 0
    