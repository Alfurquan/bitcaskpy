import click
import uuid

from .store_config import load_config, save_config
from ..client import BitcaskClient, BitcaskClientError, BitcaskConnectionError
from ..logging.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("cli")

def get_client():
    """Get BitcaskClient instance with error handling"""
    config = load_config()
    server_url = config.get("server_url", "http://localhost:8000")
    
    try:
        client = BitcaskClient(base_url=server_url)
        # Test connection
        if not client.ping():
            click.echo(f"Error: Cannot connect to BitcaskPy server at {server_url}", err=True)
            click.echo("Make sure the server is running with: bitcask-server", err=True)
            raise click.Abort()
        return client
    except BitcaskConnectionError:
        click.echo(f"Error: Cannot connect to BitcaskPy server at {server_url}", err=True)
        click.echo("Make sure the server is running with: bitcask-server", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


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
# Top-level CLI group
# -------------------------
@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, debug):
    """Bitcask CLI - HTTP client for BitcaskPy server"""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug


def debug_log(ctx, msg, **kwargs):
    if ctx.obj.get('DEBUG'):
        logger.debug(msg, **kwargs)

@cli.command()
@click.pass_context
@click.argument("key")
@click.argument("value")
def put(ctx, key, value):
    """Insert or update a key-value pair"""
    try:
        client = get_client()
        response, request_id = client.put(key, value)
        debug_log(ctx, "cli_command", operation="put", key=key, request_id=request_id)
        click.echo(f"Inserted {key} -> {value}")
    except BitcaskClientError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.pass_context
@click.argument("key")
def get(ctx, key):
    """Retrieve a value for a key"""
    try:
        client = get_client()
        value, request_id = client.get(key)
        if value is not None:
            debug_log(ctx, "cli_command", operation="get", key=key, request_id=request_id)
            click.echo(value)
        else:
            debug_log(ctx, "cli_command", operation="get", key=key, request_id=request_id, message="Key not found")
            click.echo("Key not found")
    except BitcaskClientError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.pass_context
@click.argument("key")
def delete(ctx, key):
    """Delete a key"""
    try:
        client = get_client()
        response, request_id = client.delete(key)
        click.echo(f"Deleted {key}")
        debug_log(ctx, "cli_command", operation="delete", key=key, request_id=request_id)
    except BitcaskClientError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
def health():
    """Check server health"""
    try:
        client = get_client()
        response = client.health()
        click.echo(f"Server status: {response['status']}")
        click.echo(f"Server version: {response['version']}")
    except BitcaskClientError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
def ping():
    """Test server connectivity"""
    config = load_config()
    server_url = config.get("server_url", "http://localhost:8000")
    
    try:
        client = BitcaskClient(base_url=server_url)
        if client.ping():
            click.echo(f"✓ Connected to BitcaskPy server at {server_url}")
        else:
            click.echo(f"✗ Cannot connect to BitcaskPy server at {server_url}")
    except Exception as e:
        click.echo(f"✗ Connection failed: {e}")

# -------------------------
# Add config as subcommand
# -------------------------
cli.add_command(config)
