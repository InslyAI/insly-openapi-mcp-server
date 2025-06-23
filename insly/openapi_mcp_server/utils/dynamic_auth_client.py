# MIT License
#
#
# Copyright (c) 2025 insly.ai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""Dynamic authentication client wrapper for per-request authentication support."""

import httpx
from typing import Any, Dict, Optional, Union
import json
from loguru import logger


class DynamicAuthClient(httpx.AsyncClient):
    """HTTP client wrapper that supports dynamic authentication header injection.
    
    This client intercepts requests and looks for authentication-related parameters
    in the request data. If found, it adds them to the appropriate headers
    and removes them from the request parameters.
    
    Supported authentication parameters:
    - Authorization: For Bearer tokens or Basic auth
    - X-API-Key (or other custom headers): For API key authentication
    - _bearer_token: Legacy parameter for backward compatibility
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the dynamic auth client."""
        super().__init__(*args, **kwargs)
        logger.debug("DynamicAuthClient initialized")
    
    async def request(
        self,
        method: str,
        url: Union[httpx.URL, str],
        *,
        content: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        json: Optional[Any] = None,
        params: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Override request method to inject dynamic authentication headers.
        
        Looks for authentication parameters in json/params/data and moves them to headers.
        """
        # Create a copy of headers to avoid modifying the original
        request_headers = dict(headers) if headers else {}
        
        # List of known authentication header names
        auth_headers = ['Authorization', 'X-API-Key', 'X-Api-Key', 'api-key', 'apikey']
        
        # Function to extract auth headers from a dict
        def extract_auth_headers(data_dict: Dict[str, Any]) -> Dict[str, str]:
            extracted = {}
            keys_to_remove = []
            
            for key, value in data_dict.items():
                # Check if this is an authentication header
                if key in auth_headers or key.lower().endswith('-key') or key.lower().endswith('-token'):
                    if value:
                        extracted[key] = str(value)
                        keys_to_remove.append(key)
                        logger.debug(f"Extracted auth header {key} for {method} {url}")
                
                # Handle legacy _bearer_token parameter
                elif key == '_bearer_token' and value:
                    extracted['Authorization'] = f'Bearer {value}'
                    keys_to_remove.append(key)
                    logger.debug(f"Extracted legacy _bearer_token for {method} {url}")
            
            # Remove extracted keys from the original dict
            for key in keys_to_remove:
                data_dict.pop(key)
            
            return extracted
        
        # Check for auth headers in JSON data
        if json is not None and isinstance(json, dict):
            auth_headers_found = extract_auth_headers(json)
            request_headers.update(auth_headers_found)
        
        # Check for auth headers in params
        if params is not None and isinstance(params, dict):
            auth_headers_found = extract_auth_headers(params)
            request_headers.update(auth_headers_found)
        
        # Check for auth headers in form data
        if data is not None and isinstance(data, dict):
            auth_headers_found = extract_auth_headers(data)
            request_headers.update(auth_headers_found)
        
        # Make the request with potentially modified headers
        return await super().request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=request_headers,
            **kwargs
        )


def create_dynamic_auth_client(
    base_url: str,
    default_headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> DynamicAuthClient:
    """Create a DynamicAuthClient instance.
    
    Args:
        base_url: The base URL for the API
        default_headers: Default headers to include in all requests
        **kwargs: Additional arguments to pass to httpx.AsyncClient
        
    Returns:
        A configured DynamicAuthClient instance
    """
    return DynamicAuthClient(
        base_url=base_url,
        headers=default_headers,
        **kwargs
    )