import click
from bitcaskpy_cli.store_config import load_config, save_config
import bitcaskpy


#--------------
# Store context
#--------------

class BitcaskContext:
    def __init__(self):
        self._store = None
    
    @property
    def store(self):
        if self._store is None:
            config = load_config()
            self._store = bitcaskpy.open_store(config["data_dir"])
        return self._store

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
@click.pass_context
def cli(ctx):
    """Bitcask CLI"""
    ctx.ensure_object(BitcaskContext)

@cli.command()
@click.argument("key")
@click.argument("value")
@click.pass_obj
def put(ctx, key, value):
    """Insert or update a key-value pair"""
    ctx.store.put(key, value)
    click.echo(f"Inserted {key} -> {value}")

@cli.command()
@click.argument("key")
@click.pass_obj
def get(ctx, key):
    """Retrieve a value for a key"""
    value = ctx.store.get(key)
    click.echo(value if value else "Key not found")

@cli.command()

@click.argument("key")
@click.pass_obj
def delete(ctx, key):
    """Delete a key"""
    ctx.store.delete(key)
    click.echo(f"Deleted {key}")

# -------------------------
# Add config as subcommand
# -------------------------
cli.add_command(config)
