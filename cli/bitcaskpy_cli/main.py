import click
from bitcaskpy_cli.store_config import load_config, save_config
import bitcaskpy

# -------------------------
# Config Commands
# -------------------------
@click.group()
def config():
    """Manage Bitcask configuration"""
    pass

@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    config = load_config()
    # Try to cast bool/int if possible
    if value.lower() in ("true", "false"):
        value = value.lower() == "true"
    elif value.isdigit():
        value = int(value)
    config[key] = value
    save_config(config)
    click.echo(f"Set {key} = {value}")

@config.command("list")
def config_list():
    config = load_config()
    for k, v in config.items():
        click.echo(f"{k} = {v}")

# -------------------------
# Data Commands
# -------------------------
@click.group()
def cli():
    """Bitcask CLI"""
    pass

@cli.command()
@click.argument("key")
@click.argument("value")
def put(key, value):
    """Insert or update a key-value pair"""
    config = load_config()
    db = bitcaskpy.open_store(config["data_dir"])
    db.put(key, value)
    click.echo(f"Inserted {key} -> {value}")

@cli.command()
@click.argument("key")
def get(key):
    """Retrieve a value for a key"""
    config = load_config()
    db = bitcaskpy.open_store(config["data_dir"])
    value = db.get(key)
    click.echo(value if value else "Key not found")

@cli.command()
@click.argument("key")
def delete(key):
    """Delete a key"""
    config = load_config()
    db = bitcaskpy.open_store(config["data_dir"])
    db.delete(key)
    click.echo(f"Deleted {key}")

# -------------------------
# Add config as subcommand
# -------------------------
cli.add_command(config)
