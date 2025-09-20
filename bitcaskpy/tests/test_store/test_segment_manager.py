from src.store.segment import Segment
from src.store.entry import Entry
from src.store.segment_manager import SegmentManager

import time
import pytest

DEFAULT_TEST_MAX_SEGMENT_SIZE = 1024 * 1024 * 10
DEFAULT_TEST_MAX_SEGMENT_ENTRIES = 100

@pytest.fixture
def setup_tmp_dir(tmp_path):
    yield tmp_path
    # Cleanup after test
    for child in tmp_path.iterdir():
        if child.is_file():
            child.unlink()
    tmp_path.rmdir()
    
def init_segment_manager(base_directory: str) -> SegmentManager:
    return SegmentManager(base_directory, max_segment_size=DEFAULT_TEST_MAX_SEGMENT_SIZE, max_segment_entries=DEFAULT_TEST_MAX_SEGMENT_ENTRIES)

def test_segment_manager_init_with_no_segments(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    assert manager.base_directory == str(setup_tmp_dir)
    assert isinstance(manager.segments, dict)
    assert len(manager.segments) == 1
    assert manager.active_segment_id is not None
    assert manager.next_segment_id == 1
    
def test_segment_manager_init_with_existing_segments(setup_tmp_dir):
    # Create two segments manually
    seg1 = Segment.new_segment(0, str(setup_tmp_dir), 1024, 100)
    seg2 = Segment.new_segment(1, str(setup_tmp_dir), 1024, 100)
    seg1.close()  # Make first segment inactive
    
    manager = SegmentManager(str(setup_tmp_dir))
    assert len(manager.segments) == 2
    assert manager.active_segment_id == 1
    assert manager.next_segment_id == 2

def test_segment_manager_append_entry_to_active_segment(setup_tmp_dir):
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
    
    first_result = manager.append(entry)
    second_result = manager.append(entry)
    third_result = manager.append(entry)
    
    assert first_result.segment_id == active_segment.id
    assert first_result.offset == 0
    assert first_result.entry_size == entry.size()
    assert second_result.segment_id == active_segment.id
    assert second_result.offset == entry.size()
    assert second_result.entry_size == entry.size()
    assert third_result.segment_id == active_segment.id
    assert third_result.offset == 2 * entry.size()
    assert third_result.entry_size == entry.size()
    

def test_segment_manager_append_and_rollover(setup_tmp_dir):
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
    
    # Append entries until rollover
    for _ in range(active_segment.max_entries):
        manager.append(entry)
    
    assert active_segment.num_entries == active_segment.max_entries
    assert active_segment.is_full() is True
    
    # Next append should trigger rollover
    manager.append(entry)
    new_active_segment = manager.get_active_segment()
    
    assert new_active_segment.id == active_segment.id + 1
    assert new_active_segment.num_entries == 1
    assert new_active_segment.is_active() is True
    assert active_segment.is_active() is False

def test_segment_manager_read_entry(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    entry = Entry(
        timestamp=time.time(),
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    manager.append(entry)
    active_segment = manager.get_active_segment()
    read_entry = manager.read(active_segment.id, 0)
    assert read_entry == entry
    
def test_segment_manager_read_nonexistent_segment(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    with pytest.raises(ValueError, match="Segment 999 not found"):
        manager.read(999, 0)
        
def test_segment_manager_get_segments(setup_tmp_dir):
    manager = init_segment_manager(str(setup_tmp_dir))
    segments = manager.get_segments()
    assert isinstance(segments, list)
    assert len(segments) == 1
    assert segments[0].id == manager.active_segment_id