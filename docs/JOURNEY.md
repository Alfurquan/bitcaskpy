# BitcaskPy Project Architecture and Design Decisions

This document outlines the architecture and design decisions for the BitcaskPy project, a Python implementation of a Bitcask-inspired key-value store. The project is structured to separate core functionality from command-line interface (CLI) features, allowing users to install only what they need. 

We will be going through the journey of how we arrived at this architecture, including the reasoning behind each decision.

## Inspiration

The Bitcask key-value store, originally implemented in Erlang, is known for its simplicity and performance. It uses a log-structured storage model, which allows for fast writes and efficient reads. The goal of BitcaskPy is to bring similar functionality to Python developers while maintaining the core principles of Bitcask. 

Inspired from Bitcask, I read these resources:
- [Bitcask Paper](https://riak.com/assets/bitcask-intro.pdf)
- [Bitcask on GitHub](https://github.com/basho/bitcask)

---

## Project Structure

The project is organized into two main packages:

```
/workspace/projects/logkv-store/
├── bitcaskpy/           # Core package
└── bitcask-cli/         # CLI package (separate)
```

---

## Phased Approach

I decided to take a phased approach to the project and the steps are outlined in this [document](../plan.md)

---

## Designing the app

### Core Package (`bitcaskpy`)

The core package contains the essential functionality of the key-value store. It is designed to be lightweight and dependency-free, making it easy to integrate into other projects.

#### Core components:

The core package includes the following components:

##### Entry

- Represents a single key-value pair in the store and an entry in the Write Ahead Log file.
- Contains metadata such as timestamps and size information.
- Responsible for serialization and deserialization of entries.

Each log entry is a binary blob that contains the following fields:

- **Timestamp**: The time when the entry was created, stored as a 64-bit integer representing milliseconds since the Unix epoch.
- **Tombstone**: A flag indicating whether the entry is a deletion (1)
    or an insertion/update (0). It is a header field so that deleted entries can be easily identified.
- **Key Size**: The size of the key in bytes, stored as a 32-bit integer.
- **Value Size**: The size of the value in bytes, stored as a 32
-bit integer.
- **Key**: The key itself, stored as a UTF-8 encoded string.
- **Value**: The value itself, stored as a UTF-8 encoded string.

It also has functions to serialize and deserialize entries to and from binary format along with calculating the size of an entry.

##### Segment

- Represents a log file segment in the store.
- Manages reading and writing entries to the log file.
- Handles file operations such as opening, closing, and syncing.
- It is basically the WAL file to which entries are appended.

Each segment corresponds to a single log file on disk. It has the following fields

- **Id**: A unique identifier for the segment, typically a timestamp or a sequential number.
- **File Path**: The path to the log file on disk.
- **Metadata File Path**: The path to the metadata file on disk.
- **Size**: The current size of the segment in bytes.
- **Number of Entries**: The number of entries in the segment.
- **Active**: A flag indicating whether the segment is active (open for writes) or read-only.
- **Closed**: A flag indicating whether the segment has been closed.
- **Max Size**: The maximum size of the segment in bytes before it needs to be rolled over.
- **Max num Entries**: The maximum number of entries in the segment before it needs to be rolled over.
- **Created At**: The timestamp when the segment was created.
- **Last synced At**: The timestamp when the segment was last synced to disk.
- **Sync interval in seconds**: The interval in seconds at which the segment should be synced to disk.

It also has methods to append entries, read entries, sync to disk, and close the segment.

##### Hash Table

- An in-memory hash table that maps keys to their corresponding entry metadata.
- Provides fast lookups for read operations.
- Supports basic operations such as get, put, and delete.

The hash table is a simple dictionary that maps keys to their corresponding entry metadata. It has the following fields:

- **Table**: A dictionary that maps keys to entry metadata.

Each hash table entry contains the following fields:

- **Segment ID**: The identifier of the segment where the entry is stored.
- **Entry Offset**: The offset of the entry within the segment file.
- **Entry Size**: The size of the entry in bytes.
- **Timestamp**: The timestamp when the entry was created.

##### Store

- The main interface for interacting with the key-value store.
- Manages segments and the hash table.
- Provides methods for put, get, delete, and other operations.


#### Design Decisions

1. **Dependency-Free Core**: The core package is designed to be dependency-free to ensure maximum compatibility and ease of use in various environments. This allows users to integrate the core functionality into their projects without worrying about additional dependencies.

2. **Separation of Concerns**: By separating the core functionality from the CLI, users can choose to install only what they need. This modular approach keeps the core package lightweight and focused on its primary purpose.

3. **Durability and Consistency**: We are keeping three files for each segment - the log file, an index file, and a metadata file. The log file stores the actual entries, the index file maps keys to their offsets in the log file, and the metadata file contains information about the segment (e.g., size, number of entries). This design ensures that we can efficiently locate entries and maintain consistency even in the event of crashes.

4. **Syncing of segment metadata**: We are syncing the segment metadata to disk at regular intervals (e.g., every second) to minimize data loss in case of crashes. This is a trade-off between performance and durability. Later we can make this configurable. For syncing we went through these options:
    - Metadata file per segment: Each segment has its own metadata file that is synced to disk at regular intervals. This approach is simple and ensures that each segment's metadata is always up-to-date.
    - Centralized metadata file: A single metadata file that contains information about all segments. This approach is more complex and requires careful management to avoid inconsistencies.
    - Segment headers: Storing metadata in the segment file itself. This approach can lead to fragmentation and makes it harder to manage metadata separately from the log entries.

    After evaluating these options, we decided to go with the first approach - a metadata file per segment. This approach is simple, easy to implement, and provides a good balance between performance and durability.

5. **Trade-offs for syncing**: Now we made an important trade off for syncing. We are not syncing segment metadata on every write to avoid performance degradation. Instead we are syncing when segment is first created, closed, and at regular intervals. This means that in the event of a crash, we may lose some recent writes that were not yet synced. However, this trade-off is acceptable for many use cases where performance is more critical than absolute durability.

    We considered these options when making this trade-off:
    - Sync on every write: This approach ensures maximum durability but can significantly impact performance, especially for workloads with high write throughput.
    - Sync at regular intervals: This approach provides a good balance between performance and durability. It allows for batching of writes and reduces the frequency of disk I/O operations.
    - Sync on segment close: This approach ensures that all entries in a segment are durable when the segment is closed. However, it does not provide any guarantees for entries that were written after the last sync but before the segment was closed.

    Real world approaches:

    **LSM-Tree Databases (RocksDB, LevelDB):**
    - Keep metadata in memory
    - Persist only on segment seal/close
    - Use manifest files for recovery
    - Periodic checkpointing

    **Bitcask (Riak):**
    - Hint files contain metadata
    - Built during compaction, not on every write
    - Fast startup via hint file reading

    **Apache Kafka:**
    - Index files separate from log files
    - Metadata flushed periodically, not on every message
    - Recovery rebuilds index from log if needed

    For our use case, we decided that syncing on segment creation, closure, and at regular intervals provides a good balance between performance and durability. This approach minimizes the risk of data loss while still allowing for high write throughput.

    **Key Principles:**

    - Never block writes for metadata updates
    - Sync on segment transitions (close, seal)
    - Graceful degradation - scan file if metadata missing
    - Atomic metadata writes to prevent corruption
    - Periodic metadata syncing

6. **Segment metadata file format**: For deciding the segment metadata file format we considered these options:

    -  JSON
        
        **Pros:**
        - Human readable and debuggable
        - Easy to parse and modify
        - Schema flexibility
        - Good tooling support
        
        **Cons:**
        - Larger file size
        - Slower parsing for large metadata
        - Not atomic updates without extra effort
        - Schema validation overhead

    - Binary Format (Recommended for performance)
    
        **Pros:**
        - Extremely fast read/write
        - Fixed size = atomic updates
        - Minimal storage overhead
        - Cache-friendly
        
        **Cons:**
        - Not human readable
        - Schema versioning complexity
        - Endianness concerns

    - Write-Ahead Log (WAL)
        
        **Pros:**
        - Crash recovery capabilities
        - History of changes
        - Atomic operations
        - Can replay state

        **Cons:**
        - Grows over time (needs compaction)
        - More complex to implement
        - Slower reads (need to replay)

    - Key-Value Format
    
        **Pros:**
        - Simple to parse
        - Human readable
        - Easy atomic updates with temp files
        - Lightweight

        **Cons:**
        - String parsing overhead
        - No type safety
        - Schema validation needed

    **Industry Best Practices**
    - Bitcask (Riak) - Hint Files
    - RocksDB - Manifest Files
    - Apache Kafka - Index Files
    - LevelDB - Metadata

    After evaluating these options, we decided to go with JSON for the segment metadata file format. This approach is simple, easy to implement, and provides good flexibility for future changes. While it may not be the most performant option, the ease of use and human readability outweigh the performance concerns for our use case. We can always optimize later if needed.
    For performance, we are not reading and updating the metadata file, instead we create a new temp file and rename it to the original file. This ensures atomic updates and minimizes the risk of corruption.

    **Why JSON is Perfect for Segment Metadata:**
    
    - Readable: You can cat segment_1.hint and see what's happening
    - Debuggable: Easy to inspect and modify during development
    - Atomic: The temp file + rename trick makes it crash-safe
    - Fast enough: For thousands of segments, JSON is plenty fast
    - Standard: Everyone knows JSON
    - Extensible: Easy to add new fields later

7. **Rebuilding Segment Metadata**: In the event of a crash or corruption, we can rebuild the segment metadata from the metadata file. This is done by looking up the metadata information from the .hint file. If the metadata file is missing or corrupted, we can scan the segment file to reconstruct the metadata. This ensures that we can recover from failures and maintain the integrity of the store.

    Trade-offs:
    - Rebuilding from metadata file is fast and efficient, but relies on the file being intact.
    - Scanning the segment file is slower, but guarantees recovery even if metadata is lost. Also we may loose some metadata information like active status, last synced at, etc. But this is acceptable as only administrative metadata is lost, not the actual data and we maintain integrity of the store.

8. **Segment Rolling**: We are implementing segment rolling based on size and number of entries. When a segment reaches its maximum size or number of entries, it is closed and a new segment is created. This helps in managing disk space and ensures that segments remain manageable in size.

9. **Hash Table Persistence**: The in-memory hash table is not persisted to disk. Intead the keys and their details are stored in index file. On startup, we rebuild the hash table from the index files. If an index file is missing or corrupted, we can scan the corresponding segment file to reconstruct the hash table entries. This ensures that we can recover from failures and maintain the integrity of the store.

    Analysis of this approach:

    **Recovery Time Comparison:**
    - Full scan: O(total_data_size) - ~10GB = 30+ seconds
    - Hint files: O(total_keys) - ~1M keys = 1-2 seconds
    - Hybrid: Hints + fallback scanning for missing hints

    **Storage Overhead:**
    - Hint files: ~50-100 bytes per key
    - 1M keys: ~50-100MB hint files vs ~10GB data
    - Recovery speedup: 10-50x faster startup

    **Trade-offs:**
    We are writing the keys to index file on every write.

    **Real-World Performance Impact**
    **✅ Likely FINE for most cases:**
    - Modern SSDs: Random writes are very fast (~100k IOPS)
    - OS buffering: File writes are cached, not immediate disk I/O
    - Small index entries: ~50-100 bytes vs potentially KB of data
    - Sequential writes: Both files are append-only (fast)
    
    **📈 Actual measurements from similar systems:**
    - RocksDB: Uses WAL + memtable (similar pattern) - production proven
    - Kafka: Writes to data + index files simultaneously - handles millions QPS
    - PostgreSQL: WAL + data files - enterprise database standard

    ** Index file size issue:**
    - Duplicate keys lead to larger index files
    - Delete tombstones help reclaim space
    - Large files slow to parse on startup
    - Loading 6 GB index file takes time

    **Mitigations (Will add later):**
    - Periodic compaction to remove stale entries
    - Limit index file size (e.g., 1 GB) and roll over
    - Use binary format for index files to reduce size
    - Consider bloom filters or other structures to speed up lookups

