# Bitcask-Inspired KV Store — Project Plan

This document breaks the work of building a Bitcask-inspired key-value store in Python into small, testable phases. Each phase includes goals, baby steps (tiny actionable items), acceptance criteria, suggested files/tests, and experiments. Iterate: implement → test → measure → refactor.

---

## Phase 0 — Prep (1–2 days)

- Goals
  - Understand Bitcask concepts: append-only log(s), in-memory hash index, file rotation, tombstones, compaction, fast reads.
  - Ensure Python tooling and testing are ready.

- Baby steps
  1. Read the Bitcask article and the original design notes (skim for invariants and tradeoffs).
  2. Set up a minimal Python project scaffold: virtualenv, requirements.txt, pytest, black/flake8.
  3. Create a blank repo layout: top-level package, tests folder, scripts folder.

- Acceptance
  - Project skeleton builds and tests run (initially empty tests).

- Why this matters
  - Low friction for iterating and safe refactoring.

---

## Phase 1 — Simple Append-only Log + In-memory Index (1–3 days)

- Goals
  - Implement a single-file append-only log where each write appends a key-value record.
  - Maintain an in-memory dictionary mapping keys → (file, offset, value_size).
  - Provide a tiny Python API: `open(path)`, `put(key, value)`, `get(key)`, `delete(key)`.

- Baby steps
  1. Design the public API and minimal file-format spec (record header fields: key length, value length, tombstone flag, checksum).
  2. Implement append-only writer behavior (open file in append mode, write record bytes).
  3. When putting a key, update the in-memory index with offset and length.
  4. For `get`, seek to file offset and read the value using index metadata.
  5. Implement `delete` by appending a tombstone record and removing the key from the in-memory index.
  6. Add unit tests for basic `put`/`get`/`delete` correctness.

- Acceptance
  - Can store and retrieve different-sized values reliably in a process.
  - Tests for overwrite and delete pass.

- Experiments
  - Microbenchmark write/read latency for a few sizes.

---

## Phase 2 — Crash Recovery and Index Rebuild (1–2 days)

- Goals
  - On `open()`, rebuild the in-memory index by scanning the log(s).

- Baby steps
  1. Implement a log scanner that iterates records and updates the index so the last write wins.
  2. Add simple checksums to detect truncated records; stop at corruption.
  3. Add tests that simulate abrupt process exit: write several records, then rebuild index from file and verify state.

- Acceptance
  - After restart, the store’s state matches the last consistent writes.

- Why this matters
  - Ensures durability expectations and predictable recovery.

---

## Phase 3 — File Rotation and Multiple Segments (2–4 days)

- Goals
  - Rotate to a new log file after a configured segment size (e.g., 64MB); keep old segment files for reads.
  - Maintain index that points to (segment-file, offset).

- Baby steps
  1. Implement segment naming and rotation logic when current file exceeds threshold.
  2. Modify index to include segment identifiers.
  3. Ensure `get()` searches only the index (no scanning of old files except during rebuild).
  4. Add unit tests: rotation triggers, reads across segment boundaries.

- Acceptance
  - Data written before and after rotation is readable; rotation threshold is respected.

---

## Phase 4 — Compaction (Merge) and Tombstones (3–7 days)

- Goals
  - Implement compaction (merge) to remove historical versions and tombstones and reclaim space.

- Baby steps
  1. Design compaction strategy: choose some segments to merge into a new compacted segment by copying only the latest live keys.
  2. Implement a merger process that reads old segments, writes live records to a new segment, builds a new index for that segment.
  3. Swap segments atomically (use rename) and delete old segments after swap.
  4. Add tombstone handling: deletes are preserved long enough to ensure replication/durability, then removed by compaction.
  5. Add tests for compaction correctness, atomic swap behavior, and crash during compaction (partial compaction should not break correctness).

- Acceptance
  - Compaction reclaims space and leaves store in consistent state even on crash mid-compaction.

- Experiments
  - Measure disk footprint before/after compaction and compaction throughput.

---

## Phase 5 — Durability and Crash Consistency Tuning (2–4 days)

- Goals
  - Decide durability model and implement safe flushing options (fsync per write, batched fsync, or background).

- Baby steps
  1. Add configurable durability levels: `no-fsync`, `fsync-on-append`, `periodic-fsync`.
  2. Implement atomic index persistence (if you persist index externally): write to temp file then atomic rename.
  3. Add tests that simulate sudden power loss (truncate file mid-record) and check recovery semantics for each durability mode.

- Acceptance
  - Behavior matches documented durability guarantees for each mode.

- Tradeoffs
  - Per-write fsync = stronger durability, lower throughput; batched fsync = higher throughput, potential data loss window.

---

## Phase 6 — Concurrency and Locking (2–5 days)

- Goals
  - Make the store safe under concurrent readers and writers (threads/processes).

- Baby steps
  1. Decide concurrency model: single-writer multiple-reader (Bitcask-style) or concurrent writers with file-level locking.
  2. Implement in-process locks (`threading.RLock`) for internal state; for multi-process, use a file lock mechanism.
  3. Ensure compaction runs without blocking reads; coordinate compaction and active writers.
  4. Add tests with many concurrent readers/writers verifying correctness.

- Acceptance
  - No data races or corruption in multi-threaded tests; cross-process locking prevents concurrent writers from corrupting segments.

---

## Phase 7 — Performance Improvements (1–2 weeks)

- Goals
  - Optimize for speed: use `mmap` for reads, tune serialization, batch writes, optionally compression.

- Baby steps
  1. Replace file reads for `get()` with memory-mapped reads for lower syscall overhead.
  2. Add batched writes: buffer small writes and flush at intervals; measure tradeoffs.
  3. Optional: compress values before writing, measure CPU vs. I/O benefit.
  4. Profile hotspots and optimize serialization/parsing (use `struct`, minimize allocations).

- Acceptance
  - Improved throughput/latency in microbenchmarks; document results.

- Experiments
  - Throughput and latency vs value size, fsync modes, and mmap vs read.

---

## Phase 8 — Advanced Index Enhancements (1–2 weeks)

- Goals
  - Reduce memory footprint and accelerate negative lookups for missing keys.

- Baby steps
  1. Add an on-disk persisted index snapshot to avoid full rebuild on restart; implement atomic snapshot replace.
  2. Integrate a Bloom filter per segment to quickly answer "definitely not present" queries.
  3. Consider tiered index: partial in-memory (hot keys) + on-disk mapping for cold keys.
  4. Tests for snapshot correctness, bloom filter false positive rate measurement.

- Acceptance
  - Reduced restart time and reduced memory for large keyspaces; bloom filters reduce unnecessary disk reads.

---

## Phase 9 — Testing, Benchmarks, and Observability (ongoing)

- Goals
  - Comprehensive tests: unit, integration, stress, and chaos tests; provide benchmark harness and metrics.

- Baby steps
  1. Create deterministic unit tests covering edge cases (truncated record, duplicate keys, deletes).
  2. Integration tests for restart, compaction, concurrency.
  3. Add a benchmark script (single-node) to measure operations/sec for `get`/`put`/`delete` at various sizes and concurrency levels.
  4. Add metrics (operation counters, latency histograms, disk usage) and simple logging.

- Acceptance
  - Tests reliably detect regressions; benchmark reproducible.

---

## Phase 10 — Optional: Replication / Sharding / Networking (weeks)

- Goals
  - Add basic replication (leader-follower) or sharding for distributed scenarios.

- Baby steps
  1. Implement an append-only replication stream from leader to followers (simple TCP-based tailing).
  2. Ensure idempotence: follower applies each record once; handle gaps on reconnect.
  3. Consider consistent hashing for sharding keys across multiple instances.
  4. Add tests to simulate follower lag and recovery.

- Acceptance
  - Followers converge to leader state; simple failure/reconnect scenarios handled.

---

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

## How to proceed right now (first 5 baby steps)

1. Create project skeleton and set up `pytest` + a simple `README` describing goals.
2. Write the public API design (list functions, parameters, behavior on crash) and small file-format spec.
3. Implement Phase 1 core logic (append-only writer, in-memory index) and tests for `put`/`get`/`delete`.
4. Run simple microbenchmarks for single-threaded writes and reads.
5. Iterate: add index rebuild test for Phase 2.