# Concurrency Control

## Design phase - Mapping out concurrency scenarios

In this phase we will recognize where race conditions can occur and design strategies to handle them. Now, we will just focus on identifying the scenarios.

- Hash table operations
  - Concurrent reads (GET) - Safe, no special handling needed
  - Concurrent writes (PUT/DELETE) - Potential race conditions if not handled properly

- Segment operations
  - Concurrent writes to the same segment file - Risk of data corruption
  - Concurrent reads from the same segment file - Safe, no special handling needed

- Segment rotation
  - Concurrent writes during rotation - Risk of data loss or corruption
  - Reads during rotation - Safe, but may read stale data

- Metadata syncing
  - Concurrent updates to in-memory index - Risk of inconsistency
  - Syncing to disk while updates are happening - Risk of data loss
  - Writing to .hint and .index files concurrently - Risk of corruption

