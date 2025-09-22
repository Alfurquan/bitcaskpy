# bitcaskpy

Bitcask-inspired KV store (learning project).

![architecture](./docs//images/Architecture.png)

Journey for the work documented [here](./docs/JOURNEY.md).

Architecture documented [here](./docs/ARCHITECTURE.md).


### Quick Start

1. **Setup virtual environment**

```bash
# Linux
python3 -m venv venv 

# Windows
python -m venv venv
```

2. **Install the package:**
```bash
pip install .
```

3. **Start the server:**
```bash
bitcaskpy-server
```

4. **Use the CLI:**
```bash
bitcaskpy put hello world
bitcaskpy get hello
```

### Modules

#### 1. Core
The storage engine - dependency-free core functionality.


#### 2. Server
HTTP API server providing REST endpoints for the key-value store.

**Usage:**
```bash
# Start server
bitcaskpy-server --host 0.0.0.0 --port 8000 --data-dir ./data

# Server endpoints:
# PUT /kv/{key} - Store key-value pair
# GET /kv/{key} - Retrieve value by key  
# DELETE /kv/{key} - Delete key
# GET /health - Health check
```

#### 3. Client
HTTP client library for connecting to BitcaskPy server.


**Usage:**
```python
from bitcaskpy_client import BitcaskClient

client = BitcaskClient("http://localhost:8000")
client.put("key", "value")
value = client.get("key")
```

#### 4. CLI
Command-line interface that connects to BitcaskPy server.

**Usage:**
```bash
# Configure server URL
bitcaskpy config set server_url http://localhost:8000

# Use CLI commands
bitcaskpy put key value
bitcaskpy get key
bitcaskpy delete key
bitcaskpy health
bitcaskpy ping
```

### Architecture Benefits

- **Scalability**: Multiple CLI clients can connect to one server
- **Network Access**: Remote administration capabilities
- **Long-running Process**: Server maintains state, solving metadata staleness issues
- **Clean Separation**: Each package has a single responsibility
- **Standard Protocols**: Uses HTTP/JSON for easy integration

### Phase plan

The project is divided into phases, each adding more features and complexity.
The details of each phase are documented here [plan.md](./plan.md)