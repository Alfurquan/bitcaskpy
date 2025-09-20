"""
BitcaskPy: A Python implementation of a Bitcask-like key-value store.
This package provides a fast, persistent key-value store inspired by the Bitcask design.
"""

from bitcaskpy.store.bitcask_store import BitcaskStore

__all__ = [
    "BitcaskStore"
]

__version__ = "0.1.0"

def open_store(directory: str) -> BitcaskStore:
    """
    Open a BitcaskStore at the specified directory.
    
    Args:
        directory (str): The directory where the store files are located.
        
    Returns:
        BitcaskStore: An instance of the BitcaskStore.
    """
    return BitcaskStore(directory)