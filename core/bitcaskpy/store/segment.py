from dataclasses import dataclass
import time
from .entry import Entry
from ..config.defaults import DEFAULT_MAX_SEGMENT_SIZE, DEFAULT_MAX_SEGMENT_ENTRIES, DEFAULT_METADATA_SYNC_INTERVAL_SECONDS

import os
import json

@dataclass
class Segment:
    """
    Represents a segment file in the log-structured key-value store.
    Attributes:
        id: Unique identifier for the segment.
        filepath: Path to the segment file.
        metadata_filepath: Path to the segment's metadata file.
        size: Current size of the segment in bytes.
        num_entries: Number of entries in the segment.
        active: Whether the segment is active (open for writes).
        max_size: Maximum allowed size of the segment in bytes.
        max_entries: Maximum allowed number of entries in the segment.
        closed: Whether the segment has been closed.
        created_at: Timestamp when the segment was created.
        metadata_sync_interval: Interval in seconds to sync metadata to disk.
        last_sync: Timestamp of the last metadata sync.
    """
    id: int
    filepath: str
    metadata_filepath: str
    size: int
    num_entries: int
    active: bool
    max_size: int
    max_entries: int
    closed: bool
    created_at: float
    metadata_sync_interval: int = DEFAULT_METADATA_SYNC_INTERVAL_SECONDS
    last_sync: float = time.time()
    
    def to_dict(self) -> dict:
        """
        Converts the segment metadata to a dictionary.
        Returns:
            A dictionary containing the segment metadata.
        """
        return {
            'id': self.id,
            'filepath': self.filepath,
            'metadata_filepath': self.metadata_filepath,
            'size': self.size,
            'num_entries': self.num_entries,
            'active': self.active,
            'max_size': self.max_size,
            'max_entries': self.max_entries,
            'closed': self.closed,
            'created_at': self.created_at,
            'metadata_sync_interval': self.metadata_sync_interval,
            'last_sync': self.last_sync
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Segment':
        """
        Creates a Segment object from a dictionary.
        Args:
            data: A dictionary containing the segment metadata.
        Returns:
            A Segment object.
        """
        return cls(
            id=data['id'],
            filepath=data['filepath'],
            metadata_filepath=data['metadata_filepath'],
            size=data['size'],
            num_entries=data['num_entries'],
            active=data['active'],
            max_size=data['max_size'],
            max_entries=data['max_entries'],
            closed=data['closed'],
            created_at=data['created_at'],
            metadata_sync_interval=data.get('metadata_sync_interval', DEFAULT_METADATA_SYNC_INTERVAL_SECONDS),
            last_sync=data.get('last_sync', time.time())
        )
    
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
        self._sync_metadata()
    
    def is_active(self) -> bool:
        """
        Checks if the segment is active and not closed.
        Returns:
            True if the segment is active and not closed, False otherwise.
        """
        return self.active and not self.closed
    
    def read(self, offset: int) -> Entry:
        """
        Reads an entry from the segment file at the given offset.
        Args:
            offset: The byte offset to start reading from.
        Returns:
            An Entry object read from the segment.
        """
        with open(self.filepath, 'rb') as f:
            f.seek(offset)
            
            # Read the fixed header first (17 bytes)
            header = f.read(17)
            if len(header) < 17:
                raise ValueError("Invalid entry: insufficient data")
            
            # Extract sizes from header
            key_size = int.from_bytes(header[8:12], 'big')
            value_size = int.from_bytes(header[12:16], 'big')
            
            # Read the variable parts
            variable_data = f.read(key_size + value_size)
            if len(variable_data) < key_size + value_size:
                raise ValueError("Invalid entry: truncated data")
            
            # Combine and deserialize
            full_entry_data = header + variable_data
            return Entry.deserialize(full_entry_data)
    
    @staticmethod
    def new_segment(id: int, base_path: str, max_size: int = DEFAULT_MAX_SEGMENT_SIZE, max_entries: int = DEFAULT_MAX_SEGMENT_ENTRIES) -> 'Segment':
        """
        Creates a new segment file and returns a Segment object.
        Args:
            id: Unique identifier for the segment.
            base_path: Base directory path for segment files.
            max_size: Maximum allowed size of the segment in bytes (default is DEFAULT_MAX_SEGMENT_SIZE).
            max_entries: Maximum allowed number of entries in the segment (default is DEFAULT_MAX_SEGMENT_ENTRIES).
        Returns:
            A new Segment object.
        """
        os.makedirs(base_path, exist_ok=True)
        
        filepath = f"{base_path}/segment_{id}.log"
        metadata_filepath = f"{base_path}/segment_{id}.hint"
        index_filepath = f"{filepath}.index"
        
        open(filepath, 'a').close()
        open(metadata_filepath, 'a').close()
        open(index_filepath, 'a').close()

        segment = Segment(
            id=id,
            filepath=filepath,
            metadata_filepath=metadata_filepath,
            size=0,
            num_entries=0,
            active=True,
            max_size=max_size,
            max_entries=max_entries,
            closed=False,
            created_at=time.time()
        )
        segment._sync_metadata()
        return segment
        
    @staticmethod
    def open_segment(id: int, base_path: str) -> 'Segment':
        """
        Opens an existing segment file and returns a Segment object.
        Args:
            id: Unique identifier for the segment.
            base_path: Base directory path for segment files.
        Returns:
            A Segment object representing the opened segment.
        """
        filepath = f"{base_path}/segment_{id}.log"
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Segment file {filepath} does not exist")
        
        metadata_filepath = f"{base_path}/segment_{id}.hint"
        if not os.path.exists(metadata_filepath):
            return Segment._scan_and_rebuild_metadata(id, base_path)

        with open(metadata_filepath, 'r') as f:
            metadata = json.load(f)
        
        return Segment.from_dict(metadata)
    
    @staticmethod
    def _scan_and_rebuild_metadata(id: int, base_path: str) -> 'Segment':
        """
        Scans the segment file to rebuild metadata if the metadata file is missing or corrupted.
        Args:
            id: Unique identifier for the segment.
            base_path: Base directory path for segment files.
        Returns:
            A Segment object with rebuilt metadata.
        """
        filepath = f"{base_path}/segment_{id}.log"
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Segment file {filepath} does not exist")

        metadata_filepath = f"{base_path}/segment_{id}.hint"
        size = os.path.getsize(filepath)
        num_entries = 0

        if size == 0:
            segment = Segment(
                id=id,
                filepath=filepath,
                metadata_filepath=metadata_filepath,
                size=0,
                num_entries=0,
                active=False,
                max_size=DEFAULT_MAX_SEGMENT_SIZE,
                max_entries=DEFAULT_MAX_SEGMENT_ENTRIES,
                closed=True,
                created_at=os.path.getctime(filepath)
            )
            segment._sync_metadata()
            return segment

        try:
            with open(filepath, 'rb') as f:
                offset = 0
                while offset < size:
                    if offset + 17 > size:
                        break
                    
                    f.seek(offset)
                    # Read the fixed part: timestamp(8) + key_size(4) + value_size(4) + tombstone(1)
                    fixed_part = f.read(17)

                    if len(fixed_part) < 17:
                        break
                    
                    # Extract key_size and value_size from the entry
                    key_size = int.from_bytes(fixed_part[8:12], 'big')
                    value_size = int.from_bytes(fixed_part[12:16], 'big')

                    # Calculate total entry size: fixed part (17) + key + value
                    entry_size = 17 + key_size + value_size

                    # Validate entry size is reasonable
                    if entry_size <= 0 or offset + entry_size > size:
                        break
                    
                    # Move to next entry
                    offset += entry_size
                    num_entries += 1

        except Exception as e:
            # If we can't parse the file, log the error but continue with what we have
            print(f"Warning: Error scanning segment file {filepath}: {e}")
            # num_entries will be whatever we counted before the error

        segment = Segment(
            id=id,
            filepath=filepath,
            metadata_filepath=metadata_filepath,
            size=size,
            num_entries=num_entries,
            active=False,
            max_size=DEFAULT_MAX_SEGMENT_SIZE,
            max_entries=DEFAULT_MAX_SEGMENT_ENTRIES,
            closed=True,
            created_at=os.path.getctime(filepath)
        )

        # Save the rebuilt metadata for future use
        segment._sync_metadata()
        return segment
                
    def append(self, entry_data: Entry) -> None:
        """
        Appends an entry to the segment file.
        Periodically syncs metadata to disk based on the metadata_sync_interval.
        Args:
            entry_data: The Entry object to append.
        Raises:
            ValueError: If the segment is full.
        """
        if self.is_full():
            raise ValueError("Segment is full")
    
        offset = self.size
        entry_size = entry_data.size()
        if self.size + entry_size > self.max_size:
            raise ValueError("Segment is full")
        
        if self.num_entries + 1 > self.max_entries:
            raise ValueError("Segment is full")
            
        serialized_data = entry_data.serialize()
        with open(self.filepath, 'ab') as f:
            f.write(serialized_data)
        self.size += len(serialized_data)
        self.num_entries += 1
        
        self._log_index_entry(
            key=entry_data.key.decode('utf-8', errors='ignore'),
            offset=offset,
            size=entry_data.value_size,
            timestamp=entry_data.timestamp
        )
        
        # Periodically sync metadata
        if time.time() - self.last_sync >= self.metadata_sync_interval:
            self._sync_metadata()
    
    def _log_index_entry(self, key: str, offset: int, size: int, timestamp: float):
        """
        Logs an index entry to the index file.
        Args:
            key: The key of the entry.
            offset: The byte offset of the entry in the segment file.
            size: The size of the entry in bytes.
            timestamp: The timestamp of the entry.        
        """
        
        index_filepath = f"{self.filepath}.index"
        entry_line = json.dumps({
            'key': key,
            'offset': offset,
            'size': size, 
            'timestamp': timestamp
        }) + '\n'
        
        with open(index_filepath, 'a') as f:
            f.write(entry_line)
    
    def _sync_metadata(self) -> None:
        """
        Syncs the segment metadata to disk
        """
        self.last_sync = time.time()
        temp_metadata_filepath = f"{self.metadata_filepath}.tmp"
        try:
            with open(temp_metadata_filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            os.rename(temp_metadata_filepath, self.metadata_filepath)
        except Exception:
            if os.path.exists(temp_metadata_filepath):
                os.remove(temp_metadata_filepath)
            raise
