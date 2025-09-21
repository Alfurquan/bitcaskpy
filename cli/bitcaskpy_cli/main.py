import click
from bitcaskpy_cli.store_config import load_config, save_config
from bitcaskpy_client import BitcaskClient
from bitcaskpy_client.client import BitcaskClientError, BitcaskConnectionError

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
# Data Commands
# -------------------------
@click.group()
def cli():
    """Bitcask CLI - HTTP client for BitcaskPy server"""
    pass

@cli.command()
@click.argument("key")
@click.argument("value")
def put(key, value):
    """Insert or update a key-value pair"""
    try:
        client = get_client()
        response = client.put(key, value)
        click.echo(f"Inserted {key} -> {value}")
    except BitcaskClientError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument("key")
def get(key):
    """Retrieve a value for a key"""
    try:
        client = get_client()
        value = client.get(key)
        if value is not None:
            click.echo(value)
        else:
            click.echo("Key not found")
    except BitcaskClientError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument("key")
def delete(key):
    """Delete a key"""
    try:
        client = get_client()
        response = client.delete(key)
        click.echo(f"Deleted {key}")
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
