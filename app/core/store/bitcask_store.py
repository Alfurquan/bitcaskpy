from .hash_table import HashTable
from .entry import Entry
from .segment_manager import SegmentManager
from ...logging.logger_factory import LoggerFactory
import time

class BitcaskStore:
    def __init__(self, base_directory: str):
        self.base_directory = base_directory
        self.logger = LoggerFactory.get_logger(__name__, service="bitcask-store")
        self.segment_manager = SegmentManager(base_directory)
        self.hash_table = HashTable()
        self._recover()
        
    def _recover(self):
        """
        Recover the store state from existing segments.
        """
        self.hash_table.recover_from_segment_manager(self.segment_manager)
        
    def put(self, key: str, value: str) -> None:
        """
        Store a key-value pair in the store.
        Args:
            key (str): The key to store.
            value (str): The value to store.
        """
        start = time.time()
        timestamp = time.time()
        entry = Entry(
            timestamp=timestamp,
            key_size=len(key),
            value_size=len(value),
            key=key.encode('utf-8'),
            value=value.encode('utf-8'),
            tombstone=False
        )
        append_result = self.segment_manager.append(entry)
        self.hash_table.put(key, append_result.segment_id, append_result.offset, entry.value_size, timestamp)
        
        end = time.time()
        duration_ms = (end - start) * 1000
        self.logger.info(
            "store_put", 
            key=key, 
            segment_id=append_result.segment_id,
            offset=append_result.offset,
            duration_ms=duration_ms,
            message=f"Stored key '{key}' at segment {append_result.segment_id} offset {append_result.offset}",
        )
        
        
    def get(self, key: str) -> str | None:
        """
        Retrieve a value by key from the store.
        Args:
            key (str): The key to retrieve.
        Returns:
            str: The value associated with the key or None if not found.
        """
        start = time.time()
        hash_entry = self.hash_table.get(key)
        if not hash_entry:
            return None
        
        segment = self.segment_manager.get_segment(hash_entry.segment_id)
        entry = segment.read(hash_entry.value_pos)
        if entry.tombstone:
            self.logger.info(
                "store_get_tombstone",
                key=key,
                message=f"Key '{key}' is marked as deleted (tombstone)",
            )
            return None
        
        end = time.time()
        duration_ms = (end - start) * 1000
        self.logger.info(
            "store_get_end",
            key=key,
            segment_id=hash_entry.segment_id,
            offset=hash_entry.value_pos,
            duration_ms=duration_ms,
            message=f"Retrieved key '{key}' with value size {entry.value_size} bytes",
        )
        return entry.value.decode('utf-8')
    
    def delete(self, key: str) -> None:
        """
        Delete a key-value pair from the store by marking it with a tombstone.
        Args:
            key (str): The key to delete.
        """
        start = time.time()
        timestamp = time.time()
        entry = Entry(
            timestamp=timestamp,
            key_size=len(key),
            value_size=0,
            key=key.encode('utf-8'),
            value=b'',
            tombstone=True
        )
        self.segment_manager.append(entry)
        self.hash_table.delete(key)
        
        end = time.time()
        duration_ms = (end - start) * 1000
        
        self.logger.info(
            "store_delete_end",
            key=key,
            duration_ms=duration_ms,
            message=f"Deleted key '{key}' by marking with tombstone",
        )
