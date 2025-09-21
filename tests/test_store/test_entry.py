from core.bitcaskpy.store.entry import Entry

def test_entry_roundtrip():
    original = Entry(
        timestamp=1625077765.1,
        key_size=3,
        value_size=5,
        key=b'key',
        value=b'value',
        tombstone=False
    )
    
    serialized = original.serialize()
    deserialized = Entry.deserialize(serialized)
    assert original == deserialized