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

"""Configuration module for the OpenAPI MCP Server."""

import os
from insly.openapi_mcp_server import get_caller_info, logger
from dataclasses import dataclass
from typing import Any

@dataclass
class Config:
    """Configuration for the OpenAPI MCP Server."""

    # API information
    api_name: str = 'awslabs-openapi-mcp-server'
    api_base_url: str = 'https://localhost:8000'
    api_spec_url: str = ''
    api_spec_path: str = ''

    # Authentication
    auth_type: str = 'none'  # none, basic, bearer, api_key, cognito
    auth_username: str = ''
    auth_password: str = ''
    auth_token: str = ''
    auth_api_key: str = ''
    auth_api_key_name: str = 'api_key'
    auth_api_key_in: str = 'header'  # header, query, cookie

    # Cognito authentication
    auth_cognito_client_id: str = ''
    auth_cognito_username: str = ''
    auth_cognito_password: str = ''
    auth_cognito_user_pool_id: str = ''
    auth_cognito_region: str = 'us-east-1'

    # Server configuration
    port: int = 8000
    # Default to 0.0.0.0 for container compatibility; use SERVER_HOST env var to override
    host: str = '0.0.0.0'
    path: str = '/mcp'  # HTTP endpoint path
    debug: bool = False
    message_timeout: int = 60
    version: str = '0.1.0'

def load_config(args: Any = None) -> Config:
    """Load configuration from arguments and environment variables.

    Args:
        args: Command line arguments

    Returns:
        Config: Configuration object

    """
    logger.debug('Loading configuration')

    # Get caller information for debugging
    caller_info = get_caller_info()
    logger.debug(f'Called from {caller_info}')

    # Create default config
    config = Config()

    # Load from environment variables
    env_vars = {
        # API information
        'API_NAME': (lambda v: setattr(config, 'api_name', v)),
        'API_BASE_URL': (lambda v: setattr(config, 'api_base_url', v)),
        'API_SPEC_URL': (lambda v: setattr(config, 'api_spec_url', v)),
        'API_SPEC_PATH': (lambda v: setattr(config, 'api_spec_path', v)),
        # Authentication
        'AUTH_TYPE': (lambda v: setattr(config, 'auth_type', v)),
        'AUTH_USERNAME': (lambda v: setattr(config, 'auth_username', v)),
        'AUTH_PASSWORD': (lambda v: setattr(config, 'auth_password', v)),
        'AUTH_TOKEN': (lambda v: setattr(config, 'auth_token', v)),
        'AUTH_API_KEY': (lambda v: setattr(config, 'auth_api_key', v)),
        'AUTH_API_KEY_NAME': (lambda v: setattr(config, 'auth_api_key_name', v)),
        'AUTH_API_KEY_IN': (lambda v: setattr(config, 'auth_api_key_in', v)),
        # Cognito authentication environment variables
        'AUTH_COGNITO_CLIENT_ID': (lambda v: setattr(config, 'auth_cognito_client_id', v)),
        'AUTH_COGNITO_USERNAME': (lambda v: setattr(config, 'auth_cognito_username', v)),
        'AUTH_COGNITO_PASSWORD': (lambda v: setattr(config, 'auth_cognito_password', v)),
        'AUTH_COGNITO_USER_POOL_ID': (lambda v: setattr(config, 'auth_cognito_user_pool_id', v)),
        'AUTH_COGNITO_REGION': (lambda v: setattr(config, 'auth_cognito_region', v)),
        # Server configuration
        'SERVER_PORT': (lambda v: setattr(config, 'port', int(v))),
        'SERVER_HOST': (lambda v: setattr(config, 'host', v)),
        'SERVER_PATH': (lambda v: setattr(config, 'path', v)),
        'SERVER_DEBUG': (lambda v: setattr(config, 'debug', v.lower() == 'true')),
        'SERVER_MESSAGE_TIMEOUT': (lambda v: setattr(config, 'message_timeout', int(v))),
    }

    # Load environment variables
    env_loaded = {}
    for key, setter in env_vars.items():
        if key in os.environ:
            env_value = os.environ[key]
            setter(env_value)
            env_loaded[key] = env_value

    if env_loaded:
        logger.debug(
            f'Loaded {len(env_loaded)} environment variables: {", ".join(env_loaded.keys())}'
        )

    # Load from arguments
    if args:
        if hasattr(args, 'api_name') and args.api_name:
            logger.debug(f'Setting API name from arguments: {args.api_name}')
            config.api_name = args.api_name

        if hasattr(args, 'api_url') and args.api_url:
            logger.debug(f'Setting API base URL from arguments: {args.api_url}')
            config.api_base_url = args.api_url

        if hasattr(args, 'spec_url') and args.spec_url:
            logger.debug(f'Setting API spec URL from arguments: {args.spec_url}')
            config.api_spec_url = args.spec_url

        if hasattr(args, 'spec_path') and args.spec_path:
            logger.debug(f'Setting API spec path from arguments: {args.spec_path}')
            config.api_spec_path = args.spec_path

        if hasattr(args, 'port') and args.port:
            logger.debug(f'Setting port from arguments: {args.port}')
            config.port = args.port

        if hasattr(args, 'path') and args.path:
            logger.debug(f'Setting path from arguments: {args.path}')
            config.path = args.path

        if hasattr(args, 'debug') and args.debug:
            logger.debug('Setting debug mode from arguments')
            config.debug = True

        # Authentication arguments
        if hasattr(args, 'auth_type') and args.auth_type:
            logger.debug(f'Setting auth type from arguments: {args.auth_type}')
            config.auth_type = args.auth_type

        if hasattr(args, 'auth_username') and args.auth_username:
            logger.debug('Setting auth username from arguments')
            config.auth_username = args.auth_username

        if hasattr(args, 'auth_password') and args.auth_password:
            logger.debug('Setting auth password from arguments')
            config.auth_password = args.auth_password

        if hasattr(args, 'auth_token') and args.auth_token:
            logger.debug('Setting auth token from arguments')
            config.auth_token = args.auth_token

        if hasattr(args, 'auth_api_key') and args.auth_api_key:
            logger.debug('Setting auth API key from arguments')
            config.auth_api_key = args.auth_api_key

        if hasattr(args, 'auth_api_key_name') and args.auth_api_key_name:
            logger.debug(f'Setting auth API key name from arguments: {args.auth_api_key_name}')
            config.auth_api_key_name = args.auth_api_key_name

        if hasattr(args, 'auth_api_key_in') and args.auth_api_key_in:
            logger.debug(f'Setting auth API key location from arguments: {args.auth_api_key_in}')
            config.auth_api_key_in = args.auth_api_key_in

        # Cognito authentication arguments
        if hasattr(args, 'auth_cognito_client_id') and args.auth_cognito_client_id:
            logger.debug('Setting Cognito client ID from arguments')
            config.auth_cognito_client_id = args.auth_cognito_client_id

        if hasattr(args, 'auth_cognito_username') and args.auth_cognito_username:
            logger.debug('Setting Cognito username from arguments')
            config.auth_cognito_username = args.auth_cognito_username

        if hasattr(args, 'auth_cognito_password') and args.auth_cognito_password:
            logger.debug('Setting Cognito password from arguments')
            config.auth_cognito_password = args.auth_cognito_password

        if hasattr(args, 'auth_cognito_user_pool_id') and args.auth_cognito_user_pool_id:
            logger.debug('Setting Cognito user pool ID from arguments')
            config.auth_cognito_user_pool_id = args.auth_cognito_user_pool_id

        if hasattr(args, 'auth_cognito_region') and args.auth_cognito_region:
            logger.debug(f'Setting Cognito region from arguments: {args.auth_cognito_region}')
            config.auth_cognito_region = args.auth_cognito_region

    # Log final configuration details
    logger.info(
        f'Configuration loaded: API name={config.api_name}, host={config.host}, port={config.port}, path={config.path}'
    )

    return config
