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

"""Base authentication provider."""

import functools
import httpx
from abc import ABC, abstractmethod
from insly.openapi_mcp_server import logger
from insly.openapi_mcp_server.api.config import Config
from insly.openapi_mcp_server.auth.auth_errors import (
    AuthError,
    ConfigurationError,
    format_error_message,
)
from insly.openapi_mcp_server.auth.auth_provider import AuthProvider
from typing import Any, Callable, Dict, Optional, TypeVar, cast

# Type variable for method return types
T = TypeVar('T')

class BaseAuthProvider(AuthProvider, ABC):
    """Base authentication provider.

    This abstract base class provides common functionality for all authentication providers.
    It implements the Template Method pattern for configuration validation and error handling.
    """

    def __init__(self, config: Config):
        """Initialize with configuration.

        Args:
            config: Application configuration

        """
        self._config = config
        self._is_valid = False
        self._auth_headers: Dict[str, str] = {}
        self._auth_params: Dict[str, str] = {}
        self._auth_cookies: Dict[str, str] = {}
        self._validation_error: Optional[AuthError] = None

        # Template method pattern: validate and initialize
        try:
            self._is_valid = self._validate_config()
            if self._is_valid:
                self._initialize_auth()
            else:
                self._handle_validation_error()
        except AuthError as e:
            self._validation_error = e
            self._is_valid = False
            self._log_auth_error(e)
            # Re-raise the exception for test cases to catch
            raise e
        except Exception as e:
            self._validation_error = ConfigurationError(
                f'Unexpected error during authentication provider initialization: {str(e)}'
            )
            self._is_valid = False
            self._log_auth_error(self._validation_error)
            # Re-raise the exception for test cases to catch
            raise self._validation_error

    def _initialize_auth(self) -> None:
        """Initialize authentication data after validation.

        This method is called after successful validation to set up
        headers, params, and cookies. Override in subclasses if needed.
        """
        pass

    @abstractmethod
    def _validate_config(self) -> bool:
        """Validate the configuration.

        Returns:
            bool: True if configuration is valid, False otherwise

        Raises:
            AuthError: If validation fails with a specific error

        """
        pass

    def _handle_validation_error(self) -> None:
        """Handle validation error.

        This method is called when validation fails but no exception is raised.
        It should create and log an appropriate error. Override in subclasses.
        """
        self._validation_error = ConfigurationError(
            f'Invalid configuration for {self.provider_name} authentication provider'
        )
        self._log_auth_error(self._validation_error)

    def _log_auth_error(self, error: AuthError) -> None:
        """Log an authentication error.

        Args:
            error: The authentication error

        """
        message = format_error_message(self.provider_name, error.error_type, error.message)
        logger.error(message)

        # Log additional details at debug level
        if error.details:
            logger.debug(f'Error details: {error.details}')

    def _log_validation_error(self) -> None:
        """Log validation error messages.

        This method is kept for backward compatibility.
        New implementations should use _handle_validation_error instead.
        """
        self._handle_validation_error()

    def _requires_valid_config(method: Callable[..., T]) -> Callable[..., T]:  # type: ignore
        """Ensure a method is only called with valid configuration.

        If the configuration is not valid, returns an empty result.
        """

        @functools.wraps(method)
        def wrapper(self: 'BaseAuthProvider', *args: Any, **kwargs: Any) -> T:
            if not self._is_valid:
                # Return empty result based on return type annotation
                return_type = method.__annotations__.get('return')
                if return_type == Dict[str, str]:
                    return cast(T, {})
                elif return_type == Optional[httpx.Auth]:
                    return cast(T, None)
                return cast(T, None)
            return method(self, *args, **kwargs)

        return wrapper

    @_requires_valid_config
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for HTTP requests.

        Returns:
            Dict[str, str]: Authentication headers

        """
        return self._auth_headers

    @_requires_valid_config
    def get_auth_params(self) -> Dict[str, str]:
        """Get authentication query parameters for HTTP requests.

        Returns:
            Dict[str, str]: Authentication query parameters

        """
        return self._auth_params

    @_requires_valid_config
    def get_auth_cookies(self) -> Dict[str, str]:
        """Get authentication cookies for HTTP requests.

        Returns:
            Dict[str, str]: Authentication cookies

        """
        return self._auth_cookies

    @_requires_valid_config
    def get_httpx_auth(self) -> Optional[httpx.Auth]:
        """Get authentication object for HTTPX.

        Returns:
            Optional[httpx.Auth]: Authentication object for HTTPX client

        """
        return None

    def is_configured(self) -> bool:
        """Check if the authentication provider is properly configured.

        Returns:
            bool: True if properly configured, False otherwise

        """
        return self._is_valid

    def get_validation_error(self) -> Optional[AuthError]:
        """Get the validation error if configuration is invalid.

        Returns:
            Optional[AuthError]: The validation error or None if configuration is valid

        """
        return self._validation_error

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of the authentication provider.

        Returns:
            str: Name of the authentication provider

        """
        pass
