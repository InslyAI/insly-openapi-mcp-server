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

"""Register authentication providers."""

import os
from insly.openapi_mcp_server import logger
from insly.openapi_mcp_server.auth.auth_factory import register_auth_provider

def register_auth_providers() -> None:
    """Register authentication providers based on configuration.

    This function registers only the authentication provider that is specified
    by the AUTH_TYPE environment variable or command-line argument.
    If no auth type is specified, it registers all available providers.
    """
    # Get the auth type from environment variable
    auth_type = os.environ.get('AUTH_TYPE', '').lower()

    # If no auth type is specified in the environment, register all providers
    if not auth_type:
        logger.debug('No auth type specified in environment, registering all providers')
        register_all_providers()
    else:
        # Register only the specified provider
        register_provider_by_type(auth_type)

def register_provider_by_type(auth_type: str) -> None:
    """Register a specific authentication provider by type.

    Args:
        auth_type: The type of authentication provider to register

    """
    if auth_type == 'bearer':
        from insly.openapi_mcp_server.auth.bearer_auth import BearerAuthProvider

        register_auth_provider('bearer', BearerAuthProvider)
        logger.info('Registered Bearer authentication provider')
    elif auth_type == 'basic':
        from insly.openapi_mcp_server.auth.basic_auth import BasicAuthProvider

        register_auth_provider('basic', BasicAuthProvider)
        logger.info('Registered Basic authentication provider')
    elif auth_type == 'api_key':
        from insly.openapi_mcp_server.auth.api_key_auth import ApiKeyAuthProvider

        register_auth_provider('api_key', ApiKeyAuthProvider)
        logger.info('Registered Api_Key authentication provider')
    elif auth_type == 'cognito':
        from insly.openapi_mcp_server.auth.cognito_auth import CognitoAuthProvider

        register_auth_provider('cognito', CognitoAuthProvider)
        logger.info('Registered Cognito authentication provider')
    else:
        logger.warning(f'Unknown auth type: {auth_type}, registering all providers')
        register_all_providers()

def register_all_providers() -> None:
    """Register all available authentication providers."""
    # Import all provider classes
    from insly.openapi_mcp_server.auth.api_key_auth import ApiKeyAuthProvider
    from insly.openapi_mcp_server.auth.basic_auth import BasicAuthProvider
    from insly.openapi_mcp_server.auth.bearer_auth import BearerAuthProvider

    # Register the standard providers
    register_auth_provider('bearer', BearerAuthProvider)
    logger.info('Registered Bearer authentication provider')

    register_auth_provider('basic', BasicAuthProvider)
    logger.info('Registered Basic authentication provider')

    register_auth_provider('api_key', ApiKeyAuthProvider)
    logger.info('Registered Api_Key authentication provider')

    # Only register Cognito if it's available
    try:
        from insly.openapi_mcp_server.auth.cognito_auth import CognitoAuthProvider

        register_auth_provider('cognito', CognitoAuthProvider)
        logger.info('Registered Cognito authentication provider')
    except ImportError:
        logger.debug('Cognito authentication provider not available')

# Don't register providers automatically when this module is imported
# This will be done explicitly in server.py
