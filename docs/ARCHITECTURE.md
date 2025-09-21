## Project Architecture till now

The project is organized into four main packages:

```
/workspace/projects/bitcaskpy/
├── core/           # Core package
└── cli/            # CLI package (separate)
├── server/         # Server package (separate)
└── client/         # Client package (separate)
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 USER LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  👤 Developer          👤 Admin User         👤 Remote User                    │
│  (Python Code)        (Local CLI)           (Remote CLI)                        │
│       │                    │                     │                              │
└───────┼────────────────────┼─────────────────────┼──────────────────────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────────┐    │
│  │   Core Library  │   │   HTTP Client   │   │        CLI Tool             │    │
│  │   (bitcaskpy)   │   │(bitcaskpy-client│   │   (bitcaskpy-cli)           │    │
│  │                 │   │                 │   │                             │    │
│  │ store = open_   │   │ client =        │   │ $ bitcask put key value     │    │
│  │ store("./data") │   │ BitcaskClient() │   │ $ bitcask get key           │    │
│  │ store.put(k,v)  │   │ client.put(k,v) │   │ $ bitcask health            │    │
│  └─────────────────┘   └─────────────────┘   └─────────────────────────────┘    │
│         │ Direct               │ HTTP                    │ HTTP                 │
│         │ File Access          │ Requests                │ Requests             │
└─────────┼──────────────────────┼─────────────────────────┼──────────────────────┘
          │                      │                         │
          │                      └─────────┬───────────────┘
          │                                │
          ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SERVER LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    BitcaskPy HTTP Server                                │    │
│  │                   (bitcaskpy-server)                                    │    │
│  │                                                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │                      FastAPI Router                             │    │    │
│  │  │                                                                 │    │    │
│  │  │  PUT  /kv/{key}     ←→  store.put(key, value)                   │    │    │
│  │  │  GET  /kv/{key}     ←→  store.get(key)                          │    │    │
│  │  │  DELETE /kv/{key}   ←→  store.delete(key)                       │    │    │
│  │  │  GET  /health       ←→  {"status": "healthy"}                   │    │    │
│  │  │                                                                 │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                │                                        │    │
│  │                                ▼                                        │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │              🎯 LONG-RUNNING STORE INSTANCE                     │    │    │
│  │  │                   (Solves Metadata Issue!)                      │    │    │
│  │  │                                                                 │    │    │
│  │  │  store = bitcaskpy.open_store("./data")                        │    │    │
│  │  │  • Persistent in-memory state                                  │    │    │
│  │  │  • No metadata staleness                                       │    │    │
│  │  │  • Periodic sync works correctly                               │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         BitcaskPy Core Engine                           │    │
│  │                                                                         │    │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐    │    │
│  │  │ SegmentManager  │   │   HashTable     │   │     Entry Format    │    │    │
│  │  │                 │   │                 │   │                     │    │    │
│  │  │ • Active seg    │   │ • Key→Location  │   │ • 17-byte header    │    │    │
│  │  │ • Segment       │   │ • O(1) lookups  │   │ • Timestamp         │    │    │
│  │  │   rotation      │   │ • Index rebuild │   │ • Key/Value sizes   │    │    │
│  │  │ • Recovery      │   │ • Conflict res. │   │ • Tombstone flag    │    │    │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────────┘    │    │
│  │           │                       │                       │              │    │
│  │           └───────────┬───────────┴───────────┬───────────┘              │    │
│  │                       ▼                       ▼                          │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │                    Segment Files                                │    │    │
│  │  │                                                                 │    │    │
│  │  │  segment_0.log     ←→  Append-only data entries                │    │    │
│  │  │  segment_0.hint    ←→  Metadata (size, count, status)          │    │    │
│  │  │  segment_0.log.index ←→ Key→offset mapping                     │    │    │
│  │  │                                                                 │    │    │
│  │  │  segment_1.log     ←→  Next segment when full                  │    │    │
│  │  │  segment_1.hint    ←→  Independent metadata                    │    │    │
│  │  │  segment_1.log.index ←→ Independent index                     │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data flow diagram

```
CLI Command: `bitcask put foo bar`
│
├─► 1. CLI creates HTTP client
├─► 2. HTTP PUT /kv/foo {"value": "bar"}
├─► 3. Server receives request
├─► 4. FastAPI routes to put_key()
├─► 5. store.put("foo", "bar")                    ┌─────────────────┐
├─► 6. SegmentManager.append()                    │                 │
├─► 7. Create Entry(timestamp, key, value)        │   Long-Running  │
├─► 8. Write to segment_N.log at correct offset   │   Server keeps  │
├─► 9. Update HashTable["foo"] = location         │   state in      │
├─► 10. Log to segment_N.log.index                │   memory!       │
├─► 11. Return HTTP 200 {"status": "success"}     │                 │
└─► 12. CLI displays "Inserted foo -> bar"        └─────────────────┘

CLI Command: `bitcask get foo`
│
├─► 1. CLI creates HTTP client
├─► 2. HTTP GET /kv/foo
├─► 3. Server uses SAME store instance (in memory!)
├─► 4. HashTable lookup: "foo" → segment_id, offset
├─► 5. Read from segment_N.log at offset
├─► 6. Return HTTP 200 {"key": "foo", "value": "bar", "found": true}
└─► 7. CLI displays "bar"
```

## Key Architecture Benefits

### Scalability

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLI #1    │────▶│             │◀────│   CLI #2    │
│ (laptop)    │     │             │     │ (server)    │
└─────────────┘     │             │     └─────────────┘
                    │  BitcaskPy  │
┌─────────────┐     │   Server    │     ┌─────────────┐
│ Python App  │────▶│             │◀────│ Custom Tool │
│ (web server)│     │             │     │ (monitoring)│
└─────────────┘     └─────────────┘     └─────────────┘
```

### Clean Separation of Concerns

- **Core**: Pure Python library for Bitcask storage engine
- **Server**: HTTP API server managing a long-running store instance
- **Client**: HTTP client library for easy integration
- **CLI**: Command-line tool for local and remote administration

---