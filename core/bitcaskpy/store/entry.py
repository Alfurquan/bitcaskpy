from dataclasses import dataclass
import struct

@dataclass
class Entry:
    """
    Represents a single entry in the log-structured key-value store.
    """
    timestamp: float
    key_size: int
    value_size: int
    key: bytes
    value: bytes
    tombstone: bool = False

    def is_tombstone(self) -> bool:
        """
        Checks if the entry is a tombstone (deletion marker).
        Returns:
            True if the entry is a tombstone, False otherwise.
        """
        return self.tombstone
    
    def size(self) -> int:
        """
        Returns the total size of the serialized entry in bytes.
        8 bytes for timestamp + 4 bytes for key_size + 4 bytes for value_size +
        1 byte for tombstone flag + key_size + value_size
        Returns:
            The size of the serialized entry in bytes.
        """
        return 8 + 4 + 4 + 1 + self.key_size + self.value_size
    
    def header_size(self) -> int:
        """
        Returns the size of the entry header (metadata) in bytes.
        8 bytes for timestamp + 4 bytes for key_size + 4 bytes for value_size + 1 byte for tombstone flag
        Returns:
            The size of the entry header in bytes.
        """
        return 8 + 4 + 4 + 1

    def serialize(self) -> bytes:
        """
        Serializes the entry to bytes for storage.
        Returns:
            A bytes object representing the serialized entry.
        """
        tombstone_flag = b'\x01' if self.tombstone else b'\x00'
        return (
            struct.pack('>d', self.timestamp) +
            self.key_size.to_bytes(4, 'big') +
            self.value_size.to_bytes(4, 'big') +
            tombstone_flag +
            self.key +
            self.value
        )
        
    @staticmethod
    def deserialize(data: bytes) -> 'Entry':
        """
        Deserializes bytes back into an Entry object.
        Args:
            data: A bytes object representing the serialized entry.
        Returns:
            An Entry object.
        Raises:
            ValueError: If the data is too short to be a valid Entry.
        """
        if len(data) < 17:
            raise ValueError("Data too short to be a valid Entry")
        
        timestamp = struct.unpack('>d', data[0:8])[0]
        key_size = int.from_bytes(data[8:12], 'big')
        value_size = int.from_bytes(data[12:16], 'big')
        
        expected_size = 17 + key_size + value_size
        if len(data) < expected_size:
            raise ValueError(f"Entry data too short: expected {expected_size}, got {len(data)}")

        tombstone = data[16] == 1
        key = data[17:17+key_size]
        value = data[17+key_size:17+key_size+value_size]
        return Entry(timestamp, key_size, value_size, key, value, tombstone)
