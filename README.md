# bitcaskpy

Bitcask-inspired KV store (learning project).

## Using the cli

1. Activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

2. Install the package:

   ```bash
    pip install ./core
    pip install ./cli
    ```
3. Use the `bitcask` command:
    ```bash
    bitcask put mykey myvalue
    bitcask get mykey
    bitcask delete mykey
    bitcask config list
    ```

## Quickstart (for developers)

Prerequisites: Python 3.10+ and `pip`.

1. Activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

2. Install dependencies:

   ```bash
    pip install -r requirements.txt
    ```

3. Run tests:
    ```bash
    pytest
    ```

4. Run linter:
    ```bash
    flake8 bitcaskpy tests
    ```

## Project layout

- `core/` — Core library code
- `cli/` — Command-line interface
- `tests/` — pytest tests
- `docs/` — design notes and API sketches

## Phase plan

The project is divided into phases, each adding more features and complexity.
The details of each phase are documented here [plan.md](./plan.md)