# MIT License
#
#
# Copyright (c) 2024 insly.ai
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

"""Authentication provider protocols and type definitions."""

import httpx
from insly.openapi_mcp_server.api.config import Config
from typing import Dict, Optional, Protocol, TypeVar, runtime_checkable

@runtime_checkable
class AuthProviderProtocol(Protocol):
    """Protocol defining the interface for authentication providers.

    This protocol allows for better type checking and removes the need for casting.
    """

    @property
    def provider_name(self) -> str:
        """Get the name of the authentication provider."""
        ...

    def is_configured(self) -> bool:
        """Check if the authentication provider is properly configured."""
        ...

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for HTTP requests."""
        ...

    def get_auth_params(self) -> Dict[str, str]:
        """Get authentication query parameters for HTTP requests."""
        ...

    def get_auth_cookies(self) -> Dict[str, str]:
        """Get authentication cookies for HTTP requests."""
        ...

    def get_httpx_auth(self) -> Optional[httpx.Auth]:
        """Get authentication object for HTTPX."""
        ...

# Type variable for auth provider classes that can be instantiated with a Config
T = TypeVar('T', bound=AuthProviderProtocol)

class AuthProviderFactory(Protocol):
    """Protocol for auth provider factory functions."""

    def __call__(self, config: Config) -> AuthProviderProtocol:
        """Create an authentication provider instance."""
        ...
