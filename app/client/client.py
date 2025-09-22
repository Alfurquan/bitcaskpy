import requests
import os
from typing import Optional
from urllib.parse import urljoin

class BitcaskClientError(Exception):
    """Base exception for BitcaskClient errors"""
    pass

class BitcaskConnectionError(BitcaskClientError):
    """Raised when unable to connect to server"""
    pass

class BitcaskServerError(BitcaskClientError):
    """Raised when server returns an error"""
    pass

class BitcaskClient:
    """HTTP client for BitcaskPy server"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize BitcaskClient
        
        Args:
            base_url: Server URL (default: from env BITCASK_SERVER or http://localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv('BITCASK_SERVER', 'http://localhost:8000')
        self.timeout = timeout
        
        # Ensure base_url ends with /
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request with error handling"""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise BitcaskConnectionError(f"Could not connect to server at {self.base_url}: {e}")
        except requests.exceptions.Timeout as e:
            raise BitcaskConnectionError(f"Request timed out after {self.timeout}s: {e}")
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = response.json().get('detail', str(e))
            except:
                error_detail = str(e)
            raise BitcaskServerError(f"Server error: {error_detail}")
        except requests.exceptions.RequestException as e:
            raise BitcaskClientError(f"Request failed: {e}")
    
    def put(self, key: str, value: str) -> dict:
        """
        Store a key-value pair
        
        Args:
            key: The key to store
            value: The value to store
            
        Returns:
            Server response dict
            
        Raises:
            BitcaskClientError: If the operation fails
        """
        return self._make_request(
            'PUT',
            f'kv/{key}',
            json={'value': value}
        )
    
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a value by key
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value if found, None if not found
            
        Raises:
            BitcaskClientError: If the operation fails
        """
        response = self._make_request('GET', f'kv/{key}')
        return response['value'] if response['found'] else None
    
    def delete(self, key: str) -> dict:
        """
        Delete a key
        
        Args:
            key: The key to delete
            
        Returns:
            Server response dict
            
        Raises:
            BitcaskClientError: If the operation fails
        """
        return self._make_request('DELETE', f'kv/{key}')
    
    def health(self) -> dict:
        """
        Check server health
        
        Returns:
            Health status dict
            
        Raises:
            BitcaskClientError: If the operation fails
        """
        return self._make_request('GET', 'health')
    
    def list_keys(self) -> dict:
        """
        List all keys (if supported by server)
        
        Returns:
            Keys list or message
            
        Raises:
            BitcaskClientError: If the operation fails
        """
        return self._make_request('GET', 'kv')
    
    def ping(self) -> bool:
        """
        Simple connectivity test
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            self.health()
            return True
        except BitcaskClientError:
            return False
