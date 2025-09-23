from .segment import Segment
from .entry import Entry
from ..config.defaults import DEFAULT_MAX_SEGMENT_SIZE, DEFAULT_MAX_SEGMENT_ENTRIES
from ...logging.logger_factory import LoggerFactory

import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class AppendResult:
    segment_id: int
    offset: int
    entry_size: int

class SegmentManager:
    def __init__(self, base_directory: str, max_segment_size: int = DEFAULT_MAX_SEGMENT_SIZE, max_segment_entries: int = DEFAULT_MAX_SEGMENT_ENTRIES):
        self.base_directory = base_directory
        self.segments: Dict[int, Segment] = {}
        self.active_segment_id: int = None
        self.next_segment_id: int = 0
        self.max_segment_size = max_segment_size
        self.max_segment_entries = max_segment_entries
        self.logger = LoggerFactory.get_logger(__name__, service="segment-manager")
        
        os.makedirs(base_directory, exist_ok=True)
        
        self._load_segments()
        if self.active_segment_id is None:
            self._create_active_segment()
        
    def _load_segments(self) -> None:
        """
        Load existing segments from the directory
        """
        self.logger.info(
            "segment_load",
            directory=self.base_directory,
            message=f"Loading segments from {self.base_directory}"
        )
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
        self.logger.info(
            "segment_create",
            segment_id=self.next_segment_id,
            message=f"Creating new active segment {self.next_segment_id}"
        )
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
    
    def append(self, entry: Entry) -> AppendResult:
        """
        Append an entry to the active segment, rolling over if needed
        Args:
            entry (Entry): The entry to append
        Returns:
            AppendResult: The result of the append operation
        """
        active_segment = self.get_active_segment()
        if active_segment.is_full():
            active_segment.close()
            self._create_active_segment()
            active_segment = self.get_active_segment()
        active_segment.append(entry)
        
        self.logger.info(
            "segment_append",
            segment_id=active_segment.id,
            message=f"Appended entry to segment {active_segment.id}"
        )
        
        return AppendResult(
            segment_id=active_segment.id,
            offset=active_segment.size - entry.size(),
            entry_size=entry.size()
        )
        
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
            self.logger.error(
                "segment_read",
                segment_id=segment_id,
                message=f"Segment {segment_id} not found"
            )
            raise ValueError(f"Segment {segment_id} not found")
        
        self.logger.info(
            "segment_read",
            segment_id=segment_id,
            offset=offset,
            message=f"Reading entry from segment {segment_id} at offset {offset}"
        )
        return segment.read(offset)
    
    def get_segments(self) -> List[Segment]:
        """
        Get all segments managed by this manager
        Returns:
            List[Segment]: List of all segments
        """
        return list(self.segments.values())
    
    def get_segment(self, segment_id: int) -> Segment:
        """
        Get a specific segment by ID
        Args:
            segment_id (int): The ID of the segment
        Returns:
            Segment: The requested segment
        """
        segment = self.segments.get(segment_id)
        if segment is None:
            self.logger.error(
                "segment_get",
                segment_id=segment_id,
                message=f"Segment {segment_id} not found"
            )
            raise ValueError(f"Segment {segment_id} not found")
        return segment
