from dataclasses import dataclass
from src.store.entry import Entry

import os

@dataclass
class Segment:
    """
    Represents a segment file in the log-structured key-value store.
    Attributes:
        id: Unique identifier for the segment.
        filepath: Path to the segment file.
        size: Current size of the segment in bytes.
        num_entries: Number of entries in the segment.
        active: Whether the segment is active (open for writes).
        max_size: Maximum allowed size of the segment in bytes.
        max_entries: Maximum allowed number of entries in the segment.
        closed: Whether the segment has been closed.
        created_at: Timestamp when the segment was created.
    """
    id: str
    filepath: str
    size: int
    num_entries: int
    active: bool
    max_size: int
    max_entries: int
    closed: bool
    created_at: float
    
    def is_full(self) -> bool:
        """
        Checks if the segment is full based on size or number of entries.
        Returns:
            True if the segment is full, False otherwise.
        """
        return self.size >= self.max_size or self.num_entries >= self.max_entries
    
    def close(self) -> None:
        """
        Closes the segment, marking it as inactive and preventing further writes.
        """
        self.closed = True
        self.active = False
    
    def is_active(self) -> bool:
        """
        Checks if the segment is active and not closed.
        Returns:
            True if the segment is active and not closed, False otherwise.
        """
        return self.active and not self.closed
    
    def read(self, offset: int, length: int) -> Entry:
        """
        Reads a portion of the segment file from the given offset.
        Args:
            offset: The byte offset to start reading from.
            length: The number of bytes to read.
        Returns:
            An Entry object read from the segment.
        """
        with open(self.filepath, 'rb') as f:
            f.seek(offset)
            return Entry.deserialize(f.read(length))
    
    @staticmethod
    def open_segment(id: str, base_path: str, max_size: int, max_entries: int, created_at: float) -> 'Segment':
        """
        Opens a new segment file for writing.
        Args:
            id: Unique identifier for the segment.
            base_path: Base directory path for segment files.
            max_size: Maximum allowed size of the segment in bytes.
            max_entries: Maximum allowed number of entries in the segment.
            created_at: Timestamp when the segment is created.
        Returns:
            A new Segment object.
        """
        os.makedirs(base_path, exist_ok=True)
        
        filepath = f"{base_path}/segment_{id}.log"
        open(filepath, 'a').close()
        
        return Segment(
            id=id,
            filepath=filepath,
            size=0,
            num_entries=0,
            active=True,
            max_size=max_size,
            max_entries=max_entries,
            closed=False,
            created_at=created_at
        )
        
    def append(self, entry_data: Entry) -> None:
        """
        Appends an entry to the segment file.
        Args:
            entry_data: The Entry object to append.
        Raises:
            ValueError: If the segment is full.
        """
        if self.is_full():
            raise ValueError("Segment is full")
        
        # Check if adding this entry would exceed size limit
        entry_size = entry_data.size()
        if self.size + entry_size > self.max_size:
            raise ValueError("Segment is full")
        
        # Check if adding this entry would exceed entries limit
        if self.num_entries + 1 > self.max_entries:
            raise ValueError("Segment is full")
            
        serialized_data = entry_data.serialize()
        with open(self.filepath, 'ab') as f:
            f.write(serialized_data)
        self.size += len(serialized_data)
        self.num_entries += 1