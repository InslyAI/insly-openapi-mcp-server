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
"""Dynamic authentication client wrapper for per-request Bearer token support."""

import httpx
from typing import Any, Dict, Optional, Union
import json
from loguru import logger


class DynamicAuthClient(httpx.AsyncClient):
    """HTTP client wrapper that supports dynamic Bearer token injection.
    
    This client intercepts requests and looks for a special '_bearer_token' parameter
    in the request data. If found, it adds the token to the Authorization header
    and removes it from the request parameters.
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
        """Override request method to inject dynamic Bearer tokens.
        
        Looks for '_bearer_token' in json data or params and moves it to headers.
        """
        # Create a copy of headers to avoid modifying the original
        request_headers = dict(headers) if headers else {}
        
        # Check for Bearer token in JSON data
        if json is not None and isinstance(json, dict):
            if '_bearer_token' in json:
                token = json.pop('_bearer_token')
                if token:
                    request_headers['Authorization'] = f'Bearer {token}'
                    logger.debug(f"Injected Bearer token from JSON data for {method} {url}")
        
        # Check for Bearer token in params
        if params is not None and isinstance(params, dict):
            if '_bearer_token' in params:
                token = params.pop('_bearer_token')
                if token:
                    request_headers['Authorization'] = f'Bearer {token}'
                    logger.debug(f"Injected Bearer token from params for {method} {url}")
        
        # Check for Bearer token in form data
        if data is not None and isinstance(data, dict):
            if '_bearer_token' in data:
                token = data.pop('_bearer_token')
                if token:
                    request_headers['Authorization'] = f'Bearer {token}'
                    logger.debug(f"Injected Bearer token from form data for {method} {url}")
        
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