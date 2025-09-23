import requests
import os
import uuid
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
        self.base_url = base_url or os.getenv('BITCASK_SERVER', 'http://localhost:8000')
        self.timeout = timeout
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> tuple[dict, str]:
        """
        Make HTTP request with error handling and request ID generation.
        Returns tuple: (response_json, request_id)
        """
        url = urljoin(self.base_url, endpoint)
        request_id = str(uuid.uuid4())
        headers = kwargs.pop('headers', {})
        headers['x-request-id'] = request_id
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=self.timeout,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json(), request_id
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
    
    # -------------------------
    # API methods
    # -------------------------
    def put(self, key: str, value: str) -> tuple[dict, str]:
        """Store a key-value pair; returns (response, request_id)"""
        return self._make_request('PUT', f'kv/{key}', json={'value': value})
    
    def get(self, key: str) -> tuple[Optional[str], str]:
        """Retrieve a value by key; returns (value_or_none, request_id)"""
        response, request_id = self._make_request('GET', f'kv/{key}')
        value = response['value'] if response.get('found') else None
        return value, request_id
    
    def delete(self, key: str) -> tuple[dict, str]:
        """Delete a key; returns (response, request_id)"""
        return self._make_request('DELETE', f'kv/{key}')
    
    def health(self) -> tuple[dict, str]:
        """Check server health; returns (response, request_id)"""
        return self._make_request('GET', 'health')
    
    def list_keys(self) -> tuple[dict, str]:
        """List all keys; returns (response, request_id)"""
        return self._make_request('GET', 'kv')
    
    def ping(self) -> bool:
        """Connectivity test; returns True if reachable"""
        try:
            self.health()
            return True
        except BitcaskClientError:
            return False
