from src.store.entry import Entry
from src.store.segment import Segment

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

def test_segment_open(setup_tmp_dir):
    segment = Segment.open_segment("test", str(setup_tmp_dir), 1024, 100, time.time())
    assert segment.id == "test"
    assert segment.filepath == f"{setup_tmp_dir}/segment_test.log"
    assert segment.size == 0
    assert segment.num_entries == 0
    assert segment.active is True
    assert segment.max_size == 1024
    assert segment.max_entries == 100
    assert segment.closed is False
    
    assert os.path.exists(segment.filepath)
    assert os.path.getsize(segment.filepath) == 0

def test_segment_close(setup_tmp_dir):
    segment = Segment.open_segment("test", str(setup_tmp_dir), 1024, 100, time.time())
    segment.close()
    assert segment.closed is True
    assert segment.active is False
    
def test_segment_is_active(setup_tmp_dir):
    segment = Segment.open_segment("test", str(setup_tmp_dir), 1024, 100, time.time())
    assert segment.is_active() is True
    segment.close()
    assert segment.is_active() is False
    
def test_segment_append_and_read(tmp_path):
    segment = Segment.open_segment("test", str(tmp_path), 1024, 100, time.time())
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    
    segment.append(entry)
    
    read_entry = segment.read(0, entry.size())
    assert read_entry == entry
    
def test_segment_append_exceeds_size(setup_tmp_dir):
    segment = Segment.open_segment("test", str(setup_tmp_dir), 50, 100, time.time())
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
    segment = Segment.open_segment("test", str(setup_tmp_dir), 1024, 2, time.time())
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