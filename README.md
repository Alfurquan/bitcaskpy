# bitcaskpy

Bitcask-inspired KV store (learning project).

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

- `bitcaskpy/` — package sources
- `tests/` — pytest tests
- `docs/` — design notes and API sketches

## Phase plan

The project is divided into phases, each adding more features and complexity.
The details of each phase are documented here [plan.md](./plan.md)