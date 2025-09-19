from dataclasses import dataclass
import struct

@dataclass
class Entry:
    timestamp: float
    key_size: int
    value_size: int
    key: bytes
    value: bytes
    tombstone: bool = False

    def is_tombstone(self) -> bool:
        return self.tombstone
    
    def size(self) -> int:
        # 8 (timestamp) + 4 (key_size) + 4 (value_size) + 1 (tombstone)
        return 8 + 4 + 4 + 1 + self.key_size + self.value_size

    def serialize(self) -> bytes:
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
