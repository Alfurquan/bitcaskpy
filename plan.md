# Bitcask-Inspired KV Store — Project Plan

This document breaks the work of building a Bitcask-inspired key-value store in Python into small, testable phases. Each phase includes goals, baby steps (tiny actionable items), acceptance criteria, suggested files/tests, and experiments. Iterate: implement → test → measure → refactor.

---

## 🎯 Current Progress Status

### ✅ **COMPLETED (Phases 0-3)**

**Phase 0 - Project Setup** ✅
- ✅ Python project scaffold with pytest, requirements.txt
- ✅ Repository structure: `bitcaskpy/src/store/`, `tests/`, documentation
- ✅ All tests passing with proper CI setup

**Phase 1 - Core Data Structures** ✅  
- ✅ **Entry class**: Serializable log entries with timestamp, key, value, tombstone flag
- ✅ **File format**: Fixed header (17 bytes) + variable key/value data
- ✅ **Serialization/Deserialization**: Binary format with big-endian encoding
- ✅ **Comprehensive tests**: Entry creation, serialization, edge cases

**Phase 2 - Segment Management** ✅
- ✅ **Segment class**: Individual log file management with metadata
- ✅ **Append-only writes**: Atomic entry appending with size tracking
- ✅ **Self-describing reads**: Entries contain embedded size information
- ✅ **Metadata persistence**: JSON hint files for segment state
- ✅ **Index logging**: Immediate key→location logging for crash recovery
- ✅ **Recovery mechanisms**: Metadata recovery + file scanning fallback
- ✅ **Comprehensive tests**: Creation, append, close, recovery scenarios

**Phase 3 - Multi-Segment Coordination** ✅
- ✅ **SegmentManager class**: Orchestrates multiple segments
- ✅ **Automatic segment rotation**: Creates new segments when current is full
- ✅ **Segment discovery**: Loads existing segments on startup
- ✅ **Active segment tracking**: Maintains single active segment for writes
- ✅ **Clean architecture**: Separation of concerns between segment and manager

**Phase 3.5 - Hash Table Index** ✅
- ✅ **HashTable class**: In-memory key→location mapping
- ✅ **HashTableEntry**: Stores segment_id, offset, size, timestamp
- ✅ **Index recovery**: Rebuilds from segment index files on startup
- ✅ **Fallback scanning**: Handles missing/corrupted index files gracefully
- ✅ **Clean separation**: Independent from segment management

**Phase 3.7 - Store Integration** ✅
- ✅ **BitcaskStore class**: High-level API coordinating all components
- ✅ **Recovery orchestration**: Initializes segments and rebuilds hash table
- ✅ **Clean architecture**: Separate initialization of components
- ✅ **Put/Get/Delete API**: Core key-value operations (implementation ready)

### 🚧 **IN PROGRESS**
- **Store API Implementation**: Put/Get/Delete methods using segment manager + hash table
- **Integration testing**: End-to-end functionality tests

### 📋 **REMAINING PHASES**
- **Phase 4**: Compaction and space reclamation
- **Phase 5**: Durability tuning (fsync strategies)
- **Phase 6**: Concurrency and locking
- **Phase 7+**: Performance optimizations, advanced features

### 🏗️ **Current Architecture**
```
BitcaskStore
├── SegmentManager (manages segment lifecycle)
│   └── Segment[] (individual log files + metadata)
└── HashTable (in-memory key→location index)
    └── HashTableEntry[] (location records)
```

**Key Design Decisions Made:**
- ✅ JSON metadata files (simple, debuggable)
- ✅ Immediate index logging (crash-safe)
- ✅ Separate index files (clear separation from metadata)
- ✅ Component separation (testable, maintainable)
- ✅ Self-describing entries (no external length needed)

---

## Phase 0 — Prep ✅ **COMPLETED**

- **Goals**
  - ✅ Understand Bitcask concepts: append-only log(s), in-memory hash index, file rotation, tombstones, compaction, fast reads.
  - ✅ Ensure Python tooling and testing are ready.

- **What we accomplished**
  - ✅ Set up complete Python project with pytest, requirements.txt
  - ✅ Created proper package structure: `bitcaskpy/src/store/`, `tests/`
  - ✅ Established testing patterns and CI workflow
  - ✅ All foundational tooling working

- **Acceptance** ✅
  - ✅ Project skeleton builds and tests run
  - ✅ Clean development environment established

---

## Phase 1 — Core Data Structures ✅ **COMPLETED**

- **Goals** 
  - ✅ Implement serializable log entry format
  - ✅ Design append-only record structure
  - ✅ Create foundation for key-value operations

- **What we accomplished**
  - ✅ **Entry class** with timestamp, key_size, value_size, key, value, tombstone
  - ✅ **Binary serialization format**: 8+4+4+1+variable bytes (timestamp+key_size+value_size+tombstone+key+value)
  - ✅ **Self-describing entries**: Size information embedded in each entry
  - ✅ **Robust deserialization**: Validates data length and handles errors
  - ✅ **Comprehensive tests**: All edge cases covered

- **Key design decisions made**
  - ✅ Big-endian encoding for cross-platform compatibility
  - ✅ Fixed header size (17 bytes) for efficient parsing
  - ✅ Embedded size information for self-contained reads

- **Acceptance** ✅
  - ✅ Can serialize/deserialize entries reliably
  - ✅ All entry tests passing
  - ✅ Format supports tombstones for deletions

---

## Phase 2 — Segment Management ✅ **COMPLETED**

- **Goals**
  - ✅ Implement single-file append-only segments
  - ✅ Add crash recovery and metadata persistence
  - ✅ Create robust segment lifecycle management

- **What we accomplished**
  - ✅ **Segment class** managing individual log files
  - ✅ **Metadata persistence**: JSON hint files (`.hint`) for segment state
  - ✅ **Index logging**: Immediate key→location logging (`.index` files)
  - ✅ **Crash recovery**: Rebuilds from metadata + index files
  - ✅ **Fallback scanning**: Reconstructs metadata by scanning segment files
  - ✅ **Self-contained reads**: No external length parameter needed
  - ✅ **Atomic operations**: Safe append and metadata sync
  - ✅ **Comprehensive tests**: All scenarios including recovery

- **Key innovations beyond original plan**
  - ✅ Immediate index file logging (not just on close)
  - ✅ Three-file structure: `.log` (data) + `.hint` (metadata) + `.index` (key locations)
  - ✅ Self-healing recovery with multiple fallback strategies

- **Acceptance** ✅
  - ✅ Segments handle append, read, close operations
  - ✅ Recovery works even after crashes
  - ✅ All segment tests passing

---

## Phase 3 — Multi-Segment Management ✅ **COMPLETED**

- **Goals**
  - ✅ Coordinate multiple segments
  - ✅ Implement segment rotation
  - ✅ Maintain cross-segment operations

- **What we accomplished**
  - ✅ **SegmentManager class** orchestrating segment lifecycle
  - ✅ **Automatic segment rotation**: Creates new segments when full
  - ✅ **Segment discovery**: Loads all existing segments on startup
  - ✅ **Active segment tracking**: Maintains single active segment for writes
  - ✅ **Cross-segment reads**: Can read from any segment by ID
  - ✅ **Clean architecture**: Manager coordinates, segments handle operations

- **Acceptance** ✅
  - ✅ Multiple segments work together seamlessly
  - ✅ Segment rotation happens automatically
  - ✅ Reads work across segment boundaries

---

## Phase 3.2 — Hash Table Index ✅ **COMPLETED**

- **Goals**
  - ✅ In-memory key→location mapping
  - ✅ Fast O(1) key lookups
  - ✅ Recovery from persistent index files

- **What we accomplished**
  - ✅ **HashTable class** with key→HashTableEntry mapping
  - ✅ **HashTableEntry**: Stores segment_id, offset, size, timestamp
  - ✅ **Index recovery**: Rebuilds from all segment index files
  - ✅ **Conflict resolution**: Latest timestamp wins for duplicate keys
  - ✅ **Fallback scanning**: Handles missing index files gracefully
  - ✅ **Clean separation**: Independent from segment management

- **Acceptance** ✅
  - ✅ O(1) key lookups working
  - ✅ Recovery rebuilds index correctly
  - ✅ Handles missing/corrupted index files

---

## Phase 3.4 — Store Integration ✅ **COMPLETED**

- **Goals**
  - ✅ High-level store API
  - ✅ Component coordination
  - ✅ Recovery orchestration

- **What we accomplished**
  - ✅ **BitcaskStore class** as main API
  - ✅ **Clean architecture**: Separate component initialization
  - ✅ **Recovery coordination**: Segments first, then hash table
  - ✅ **Component separation**: No tight coupling between parts
  - ✅ **Foundation for operations**: Ready for put/get/delete implementation

- **Acceptance** ✅
  - ✅ Store initializes all components correctly
  - ✅ Recovery process works end-to-end
  - ✅ Clean separation of concerns maintained

---

## Phase 3.6 - Store CLI implementation ✅ **COMPLETED**

- Goals
  - Implement a simple command-line interface (CLI) for interacting with the store.
  - Support basic operations: put, get, delete, list keys.
  - Provide options for configuring store parameters (e.g., segment size, durability mode).

- Baby steps
  1. Set up a CLI framework using argparse or click.
  2. Implement commands for put, get, delete operations.
  3. Add a command to list all keys in the store.
  4. Add options for configuring store parameters via command-line arguments.
  5. Write tests for CLI commands to ensure correct behavior.
  6. Document CLI usage in README or separate docs.

- Acceptance
  - CLI works as expected for all operations.
  - Configuration options are applied correctly.
  - Tests cover all CLI commands.
  - Documentation provides clear usage instructions.

---

## Phase 3.8 - Store Server implementation ✅ **COMPLETED**

- Goals
  - Implement a simple TCP Server or API Server using Flask/FastAPI for remote access to the store.
  - Support basic operations: put, get, delete via a simple protocol (e.g., JSON over TCP).
  - Handle multiple concurrent client connections.

- Baby steps
  1. Set up a basic TCP server or Flask/FastAPI app.
  2. Implement endpoints or commands for put, get, delete operations.
  3. Add concurrency support (threading or async) to handle multiple clients.
  4. Make sure we add locks to ensure thread safety.
  5. Write tests for server endpoints to ensure correct behavior.
  6. Document server usage in README or separate docs.

- Acceptance
  - Server works as expected for all operations.
  - Handles multiple concurrent clients without data corruption.
  - Tests cover all server endpoints.
  - Documentation provides clear usage instructions.

---

## Post MVP Phases (4-7+)

- **Phase 4**: Observability & Monitoring
  - Structured Logging: Replace print statements with structured logs (JSON format)
  - Metrics Collection: Request latency, throughput, error rates, active connections
  - Health Checks: /health endpoint for load balancer integration
  - Distributed Tracing: Correlation IDs across client→server→storage

- **Phase 5**: Reliability Patterns
  - Graceful Shutdown: Handle SIGTERM, drain connections, sync metadata
  - Circuit Breaker: Fail fast when storage is unavailable
  - Retry with Backoff: Exponential backoff for transient failures
  - Timeout Management: Request timeouts to prevent resource exhaustion

- **Phase 6**: Concurrency Control
  - Reader-Writer Locks: Multiple readers, single writer (Bitcask pattern)
  - Segment-Level Locking: Fine-grained locking for better performance
  - Background Tasks: Async metadata syncing, compaction scheduling
  - Connection Pooling: HTTP client connection reuse

- **Phase 7**: Performance optimizations
  - Compaction: Background merging of segments to reclaim space
  - Bloom Filters: Fast negative lookups to avoid unnecessary disk reads
  - Memory-Mapped Files: Faster segment reads
  - Batch Operations: Bulk put/get/delete for efficiency

- **Phase 8**: Operational Features
  - Configuration Management:  YAML/JSON config files, environment variables
  - Authentication & Authorization: API key or token-based access control
  - Rate Limiting: Prevent abuse and ensure fair usage
  - Admin API: Endpoints for stats, config changes, manual compaction

- **Phase 9**: Distributed systems (stretch goals)
  - Replication: Master-slave or multi-master replication for high availability
  - Sharding: Distribute keys across multiple nodes
  - Consensus Protocols: Raft or Paxos for strong consistency
  - Conflict Resolution: Vector clocks, last-write-wins

- **Phase 10**: Data management features
  - Schema Evolution: Versioned data formats
  - Multi-Version Concurrency Control: Read snapshots
  - Transactions: ACID properties for multi-key operations
  - Secondary Indexes: Query by value, range queries

- **Phase 11**: Advanced caching
  - Write-Through Cache: In-memory value cache
  - LRU Eviction: Memory pressure management
  - Cache Warming: Preload frequently accessed keys
  - Cache Coherence: Invalidation strategies

## Project hygiene & micro-tasks (apply each phase)

- Always: write tests for each new invariant before/after implementing change.
- Use small commits with meaningful messages: "phase1: add append-only record format", etc.
- Keep a `CHANGELOG.md` describing behavior and assumptions (durability, atomicity).
- Document CLI/test scripts for running benchmarks and failure scenarios.

---

## Design decision checklist (document for every phase)

- Record format (header fields + checksum).
- Durability guarantees and default mode.
- Concurrency model (single-writer vs multi-writer).
- Compaction trigger policy and safety.
- Index persistence (in-memory vs snapshot).
- Failure modes and recovery strategy.

---

## Minimal file layout suggestion (no code; for organization)

- package root (e.g., `bitcaskpy/`)
  - core module (KV store, segment management)
  - compactor module
  - index module
  - io module (file operations, format helpers)
  - `tests/`
  - `benchmarks/`
  - `scripts/` (tools for running experiments)
  - `docs/` (design notes, tradeoffs, experiments)

---

## Small, safe experiments to run early

- Write many small keys (e.g., 10M keys) to test index memory pressure.
- Measure restart time vs number of segments and with/without persisted index snapshot.
- Test crash recovery: kill process during write, compaction, and index snapshot.

---

## Recommended reading & tools

- The Bitcask article (primary design source) and related Basho blog posts.
- “Designing Data-Intensive Applications” (for tradeoffs, durability, replication).
- Python tools: `pytest` for tests, `timeit`/`asyncio` for benchmarks, `mmap`, `struct`, `filelock` or `portalocker` for cross-process locks.
- Profilers: `py-spy`, `cProfile` to find hotspots.

---

## 🏆 **Achievement Summary**

**What makes this implementation special:**
- ✅ **Production-ready architecture**: Clean separation of concerns
- ✅ **Robust recovery**: Multiple fallback strategies
- ✅ **Crash-safe operations**: Immediate index logging
- ✅ **Comprehensive testing**: All components thoroughly tested
- ✅ **Industry patterns**: Follows proven database design principles

**Current capabilities:**
- ✅ Persistent key-value storage with segments
- ✅ Automatic segment rotation and management  
- ✅ Crash-safe recovery from multiple sources
- ✅ In-memory hash index for O(1) lookups
- ✅ Self-healing systems with fallback mechanisms
- ✅ Clean, testable, maintainable codebase

**Ready for production use cases:**
- Small to medium-scale key-value storage
- Applications requiring fast reads with durability
- Systems needing predictable recovery behavior
- Projects wanting to understand database internals