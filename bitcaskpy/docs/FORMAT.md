# Format

The data is stored in a log-structured format, with each entry consisting of a key-value pair. The log is periodically compacted to improve read performance and reclaim disk space.

## Log Entry Format

Each log entry is a binary blob that contains the following fields:

- **Timestamp**: The time when the entry was created, stored as a 64-bit integer representing milliseconds since the Unix epoch.
- **Tombstone**: A flag indicating whether the entry is a deletion (1) or an insertion/update (0). It is a header field so that deleted entries can be easily identified.
- **Key Size**: The size of the key in bytes, stored as a 32-bit integer.
- **Value Size**: The size of the value in bytes, stored as a 32-bit integer.
- **Key**: The key itself, stored as a UTF-8 encoded string.
- **Value**: The value itself, stored as a UTF-8 encoded string.

## Segment Entry Format

Each segment entry consists of multiple log entries concatenated together. The segment file begins with a header that contains metadata about the segment:

- **Segment ID**: A unique identifier for the segment, stored as a UUID.
- **Creation Time**: The time when the segment was created, stored as a 64-bit integer representing milliseconds since the Unix epoch.
- **Number of Entries**: The total number of log entries in the segment, stored as a 32-bit integer.
- **Path**: The file path of the segment, stored as a UTF-8 encoded string.
- **Size**: The total size of the segment in bytes, stored as a 64-bit integer.
- **Max Size**: The maximum allowed size of the segment in bytes, stored as a 64-bit integer.
- **Max Entries**: The maximum number of entries allowed in the segment, stored as a 32-bit integer.
- **Active**: A flag indicating whether the segment is active (1) or inactive (0).
- **Closed**: A flag indicating whether the segment is closed (1) or open (0).


## Encoding policy

- Keys and values are encoded using UTF-8.
- The log entry format is designed to be efficient for both storage and retrieval.
