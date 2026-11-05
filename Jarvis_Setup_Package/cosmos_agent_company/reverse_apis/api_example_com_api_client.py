"""
Reverse-Engineered Client for api.example.com
Synthesized automatically by COSMOS (Sri Charan Tirumaladasu)
Executes direct sub-200ms HTTP requests using requests.Session() with connection pooling.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Any, Dict, List, Optional


class ApiExampleComClient:
    """Autonomous high-speed API client for api.example.com."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or "https://api.example.com").rstrip("/")
        self.session = requests.Session()
        
        # Configure robust connection pooling & exponential backoff retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(pool_connections=15, pool_maxsize=30, max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Preload extracted authentication headers and CSRF tokens
        self.default_headers = {
        "Authorization": "Bearer secret_jwt_token_12345",
        "X-CSRF-Token": "csrf_token_abc"
}
        self.default_headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        self.session.headers.update(self.default_headers)

        # Preload active session cookies
        self.session.cookies.update({})
        
        self.pagination_keys = ["limit", "page"]

    def get_v1_users(self, params: Optional[Dict[str, Any]] = None, page: int = 1, limit: int = 20, timeout: float = 10.0) -> Dict[str, Any]:
        """Executes GET on /v1/users."""
        url = f"{self.base_url}/v1/users"
        req_params = dict(params or {})
        if 'page' in self.pagination_keys:
            req_params['page'] = page
        elif 'offset' in self.pagination_keys:
            req_params['offset'] = (page - 1) * limit
        if 'limit' in self.pagination_keys:
            req_params['limit'] = limit
        try:
            response = self.session.request(method='GET', url=url, params=req_params, timeout=timeout)
            response.raise_for_status()
            return response.json() if 'application/json' in response.headers.get('content-type', '') else {'text': response.text, 'status': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'error': str(e), 'status': getattr(getattr(e, 'response', None), 'status_code', 500), 'url': url}

    def post_v1_orders(self, payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Executes POST on /v1/orders."""
        url = f"{self.base_url}/v1/orders"
        req_params = dict(params or {})
        try:
            response = self.session.request(method='POST', url=url, params=req_params, timeout=timeout, json=payload)
            response.raise_for_status()
            return response.json() if 'application/json' in response.headers.get('content-type', '') else {'text': response.text, 'status': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'error': str(e), 'status': getattr(getattr(e, 'response', None), 'status_code', 500), 'url': url}

