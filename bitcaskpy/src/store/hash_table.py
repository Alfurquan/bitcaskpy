from dataclasses import dataclass
import json
import os
from typing import Dict

from src.store.segment_manager import SegmentManager
from src.store.segment import Segment

@dataclass
class HashTableEntry:
    segment_id: int
    value_size: int
    value_pos: int
    timestamp: float
    
    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "value_size": self.value_size,
            "value_pos": self.value_pos,
            "timestamp": self.timestamp
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'HashTableEntry':
        return HashTableEntry(
            segment_id=data["segment_id"],
            value_size=data["value_size"],
            value_pos=data["value_pos"],
            timestamp=data["timestamp"]
        )
        
class HashTable:
    def __init__(self):
        self.table: Dict[str, HashTableEntry] = {}
        
    def recover_from_segment_manager(self, segment_manager: SegmentManager) -> None:
        """
        Recover the hash table from the segment manager's segments
        Args:
            segment_manager (SegmentManager): The segment manager to recover from
        """
        for segment in segment_manager.get_segments():
            self._recover_from_segment(segment)
            
    def _recover_from_segment(self, segment) -> None:
        """
        Recover entries from a single segment
        Args:
            segment (Segment): The segment to recover from
        """
        index_file_path = f"{segment.filepath}.index"
        if os.path.exists(index_file_path):
            self._load_from_index_file(segment, index_file_path)
        else:
            self._rebuild_from_segment_scan(segment)
            
    def _load_from_index_file(self, segment: Segment, index_file_path: str) -> None:
        """
        Load hash table entries from an index file
        Args:
            segment (Segment): The segment associated with the index file
            index_file_path (str): Path to the index file
        """
        try:
            with open(index_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        key = entry['key']

                        existing = self.table.get(key)
                        if not existing or entry['timestamp'] > existing.timestamp:
                            self.table[key] = HashTableEntry(
                                segment_id=segment.id,
                                value_size=entry['size'],
                                value_pos=entry['offset'],
                                timestamp=entry['timestamp']
                            )
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error parsing line {line_num} in index file {index_file_path}: {e}")
                        continue
        
        except Exception as e:
            print(f"Error loading index file {index_file_path}: {e}")
            self._rebuild_from_segment_scan(segment)
            
    def _rebuild_from_segment_scan(self, segment: Segment) -> None:
        """
        Rebuild the hash table by scanning the segment file
        Args:
            segment (Segment): The segment to scan
        """
        if segment.size == 0:
            return
        
        try:
            offset = 0
            while offset < segment.size:
                entry = segment.read(offset)
                entry_size = entry.size()
                
                key = entry.key.decode('utf-8', errors='ignore')
                existing = self.table.get(key)
                if not existing or entry.timestamp > existing.timestamp:
                    self.table[key] = HashTableEntry(
                        segment_id=segment.id,
                        value_size=entry.value_size,
                        value_pos=offset + entry.header_size() + entry.key_size,
                        timestamp=entry.timestamp
                    )
                
                offset += entry_size
        except Exception as e:
            print(f"Error scanning segment {segment.id}: {e}")
    
    def get(self, key: str) -> HashTableEntry:
        """
        Get the hash table entry for a given key
        Args:
            key (str): The key to look
        Returns:
            HashTableEntry: The corresponding hash table entry
        """
        return self.table.get(key)
    
    def put(self, key: str, segment_id: int, offset: int, size: int, timestamp: float) -> None:
        """
        Put or update a hash table entry
        Args:
            key (str): The key to insert/update
            segment_id (int): The segment ID where the value is stored
            offset (int): The offset within the segment
            size (int): The size of the value
            timestamp (float): The timestamp of the entry
        """
        self.table[key] = HashTableEntry(
            segment_id=segment_id,
            value_size=size,
            value_pos=offset,
            timestamp=timestamp
        )
        
    def delete(self, key: str) -> None:
        """
        Delete a key from the hash table
        Args:
            key (str): The key to delete
        """
        if key in self.table:
            del self.table[key]
            
    def size(self) -> int:
        """
        Get the number of entries in the hash table
        Returns:
            int: The number of entries
        """
        return len(self.table)
