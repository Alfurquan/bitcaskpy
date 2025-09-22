import os
import json

CONFIG_PATH = os.path.expanduser("~/.bitcask/config.json")

DEFAULT_CONFIG = {
    "data_dir": "./data",
    "server_url": "http://localhost:8000",
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        return {**DEFAULT_CONFIG, **cfg}  # merge defaults
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
