# API

## Overview

The API provides a set of functions for interacting with the key-value store. It allows users to perform basic operations such as adding, retrieving, and deleting key-value pairs.

## Functions

### `put(key: str, value: str) -> None`

Adds a new key-value pair to the store. Overwrites the value if the key already exists.

#### Parameters

- `key`: The key under which the value is stored.
- `value`: The value to be stored.

#### Exceptions
- Raises `ValueError` if the key or value exceeds the maximum allowed size.
- Raises `IOError` if there is an issue writing to the storage.
- Raises `TypeError` if the key or value is not a string.

### `get(key: str) -> Optional[str]`

Retrieves the value associated with the given key. Deleted/tombstoned keys return `None`.

#### Parameters

- `key`: The key for which the value is to be retrieved.

#### Returns

- The value associated with the key, or `None` if the key does not exist.

### `delete(key: str) -> None`

Removes the key-value pair associated with the given key. If key does not exist, the operation is a no-op.

#### Parameters

- `key`: The key to be removed.

## Lifecycle functions

### `open_store(path: str) -> None`

Opens the key-value store located at the specified path. If the store does not exist, it will be created. By default, the store is opened in read-write mode at location `./data`.

#### Parameters

- `path`: The file path where the store is located or should be created.

#### Exceptions

- Raises `IOError` if there is an issue accessing the specified path.

### `close_store() -> None`

Closes the key-value store, ensuring all data is flushed to disk and resources are released.

#### Exceptions
- Raises `IOError` if there is an issue during the closing process.

## Durability options

- `sync`: If set to `True`, every write operation is immediately flushed to disk. Default is `False` for better performance.

- `fsync_interval`: If `sync` is `False`, this option specifies the interval (in seconds) at which data is flushed to disk. Default is `5` seconds.

- `fsync_on_append`: If set to `True`, the store will perform an `fsync` operation after every append operation. Default is `False`.

- `max_segment_size`: The maximum size (in bytes) of each segment file before a new segment is created. Default is `10485760` bytes (10 MB).

- `max_entries_per_segment`: The maximum number of entries allowed in each segment before a new segment is created. Default is `1000`.

## Size and Capacity

- Maximum key size: 1 KB
- Maximum value size: Configurable (default: 1 MB)

## Configure durability and size options

All durability and size options can be configured when opening the store using the `open_store` function. Example:

```python
open_store(path='./data', sync=True, fsync_interval=10, max_segment_size=20971520, max_entries_per_segment=2000)
```

Or we can set them using environment variables:
```python
export BITCASKPY_SYNC=True
export BITCASKPY_FSYNC_INTERVAL=10
export BITCASKPY_MAX_SEGMENT_SIZE=20971520
export BITCASKPY_MAX_ENTRIES_PER_SEGMENT=2000
```

## Concurrency

The API is designed to be thread-safe, allowing concurrent access from multiple threads. Internal locking mechanisms ensure data integrity during read and write operations.

