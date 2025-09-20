from src.store.segment import Segment
from src.store.entry import Entry
from src.config.defaults import DEFAULT_MAX_SEGMENT_SIZE, DEFAULT_MAX_SEGMENT_ENTRIES

import os
from typing import Dict

class SegmentManager:
    def __init__(self, base_directory: str, max_segment_size: int = DEFAULT_MAX_SEGMENT_SIZE, max_segment_entries: int = DEFAULT_MAX_SEGMENT_ENTRIES):
        self.base_directory = base_directory
        self.segments: Dict[int, Segment] = {}
        self.active_segment_id: int = None
        self.next_segment_id: int = 0
        self.max_segment_size = max_segment_size
        self.max_segment_entries = max_segment_entries
        
        os.makedirs(base_directory, exist_ok=True)
        
        self._load_segments()
        if self.active_segment_id is None:
            self._create_active_segment()
        
    def _load_segments(self) -> None:
        """
        Load existing segments from the directory
        """
        for filename in os.listdir(self.base_directory):
            if filename.startswith("segment_") and filename.endswith(".log"):
                 segment_id = int(filename.split("_")[1].split(".")[0])
                 segment = Segment.open_segment(segment_id, self.base_directory)
                 self.segments[segment_id] = segment
                 if segment.is_active():
                      self.active_segment_id = segment_id
                 self.next_segment_id = max(self.next_segment_id, segment_id + 1)
         
    def _create_active_segment(self) -> None:
        """
        Create a new active segment
        """
        segment = Segment.new_segment(self.next_segment_id, self.base_directory, self.max_segment_size, self.max_segment_entries)
        self.segments[self.next_segment_id] = segment
        self.active_segment_id = self.next_segment_id
        self.next_segment_id += 1
        
    def get_active_segment(self) -> Segment:
        """
        Get the current active segment
        Returns:
            Segment: The active segment
        """
        return self.segments[self.active_segment_id]
    
    def append(self, entry: Entry) -> None:
        """
        Append an entry to the active segment, rolling over if needed
        Args:
            entry (Entry): The entry to append
        """
        active_segment = self.get_active_segment()
        if active_segment.is_full():
            active_segment.close()
            self._create_active_segment()
            active_segment = self.get_active_segment()
        active_segment.append(entry)
        
    def read(self, segment_id: int, offset: int) -> Entry:
        """
        Read an entry from a specific segment at a given offset
        Args:
            segment_id (int): The ID of the segment
            offset (int): The offset within the segment
        Returns:
            Entry: The read entry
        """
        segment = self.segments.get(segment_id)
        if segment is None:
            raise ValueError(f"Segment {segment_id} not found")
        return segment.read(offset)
    