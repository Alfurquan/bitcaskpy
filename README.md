# bitcaskpy

Bitcask-inspired KV store (learning project).

Journey for the work documented [here](./docs/JOURNEY.md).

Architecture documented [here](./docs/ARCHITECTURE.md).


### Quick Start

1. **Install all packages:**
```bash
pip install ./core
pip install ./server
pip install ./client
pip install ./cli
```

2. **Start the server:**
```bash
bitcask-server
```

3. **Use the CLI:**
```bash
bitcask put hello world
bitcask get hello
```

### Packages

#### 1. Core (`core/bitcaskpy`)
The storage engine - dependency-free core functionality.

**Installation:**
```bash
cd core && pip install -e .
```

**Usage:**
```python
import bitcaskpy
store = bitcaskpy.open_store("./data")
store.put("key", "value")
value = store.get("key")
```

#### 2. Server (`server/bitcaskpy-server`)
HTTP API server providing REST endpoints for the key-value store.

**Installation:**
```bash
cd server && pip install -e .
```

**Usage:**
```bash
# Start server
bitcask-server --host 0.0.0.0 --port 8000 --data-dir ./data

# Server endpoints:
# PUT /kv/{key} - Store key-value pair
# GET /kv/{key} - Retrieve value by key  
# DELETE /kv/{key} - Delete key
# GET /health - Health check
```

#### 3. Client (`client/bitcaskpy-client`)
HTTP client library for connecting to BitcaskPy server.

**Installation:**
```bash
cd client && pip install -e .
```

**Usage:**
```python
from bitcaskpy_client import BitcaskClient

client = BitcaskClient("http://localhost:8000")
client.put("key", "value")
value = client.get("key")
```

#### 4. CLI (`cli/bitcaskpy-cli`)
Command-line interface that connects to BitcaskPy server.

**Installation:**
```bash
cd cli && pip install -e .
```

**Usage:**
```bash
# Configure server URL
bitcask config set server_url http://localhost:8000

# Use CLI commands
bitcask put key value
bitcask get key
bitcask delete key
bitcask health
bitcask ping
```

### Architecture Benefits

- **Scalability**: Multiple CLI clients can connect to one server
- **Network Access**: Remote administration capabilities
- **Long-running Process**: Server maintains state, solving metadata staleness issues
- **Clean Separation**: Each package has a single responsibility
- **Standard Protocols**: Uses HTTP/JSON for easy integration

### Dependencies

- **Core**: No external dependencies
- **Server**: FastAPI, Uvicorn, depends on Core
- **Client**: Requests
- **CLI**: Click, depends on Client

### Development

Each package can be developed and versioned independently. The server solves the metadata staleness issue by maintaining a long-running process with the storage engine.

### Phase plan

The project is divided into phases, each adding more features and complexity.
The details of each phase are documented here [plan.md](./plan.md)