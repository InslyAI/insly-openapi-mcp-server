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

"""insly openapi MCP Server implementation."""

import argparse
import asyncio
import httpx
import re
import signal
import sys

# Import from our modules - use direct imports from sub-modules for better patching in tests
from insly.openapi_mcp_server import logger
from insly.openapi_mcp_server.api.config import Config, load_config
from insly.openapi_mcp_server.prompts import MCPPromptManager
from insly.openapi_mcp_server.utils.http_client import HttpClientFactory, make_request_with_retry
from insly.openapi_mcp_server.utils.metrics_provider import metrics
from insly.openapi_mcp_server.utils.openapi import load_openapi_spec
from insly.openapi_mcp_server.utils.openapi_validator import validate_openapi_spec
from insly.openapi_mcp_server.utils.tool_naming import generate_mcp_names, validate_tool_names
from insly.openapi_mcp_server.utils.description_enhancer import enhance_tool_descriptions
from fastmcp import FastMCP
from typing import Any, Dict

def create_mcp_server(config: Config) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        config: Server configuration

    Returns:
        FastMCP: The configured FastMCP server

    """
    # Log environment information
    logger.debug('Environment information:')
    logger.debug(f'Python version: {sys.version}')
    try:
        logger.debug(f'HTTPX version: {httpx.__version__}')
    except AttributeError:
        logger.debug('HTTPX version: unknown')

    logger.info('Creating FastMCP server')

    try:
        # Load OpenAPI spec
        if not config.api_spec_url and not config.api_spec_path:
            logger.error('No API spec URL or path provided')
            raise ValueError('Either api_spec_url or api_spec_path must be provided')

        logger.debug(
            f'Loading OpenAPI spec from URL: {config.api_spec_url} or path: {config.api_spec_path}'
        )
        openapi_spec = load_openapi_spec(url=config.api_spec_url, path=config.api_spec_path)

        # Validate the OpenAPI spec
        if not validate_openapi_spec(openapi_spec):
            logger.warning('OpenAPI specification validation failed, but continuing anyway')

        # Create a client for the API
        if not config.api_base_url:
            logger.error('No API base URL provided')
            raise ValueError('API base URL must be provided')

        # Configure authentication using the auth factory
        from insly.openapi_mcp_server.auth import get_auth_provider, is_auth_type_available

        # Import and register the specific auth provider
        from insly.openapi_mcp_server.auth.register import register_provider_by_type

        # Register only the provider we need
        if config.auth_type and config.auth_type != 'none':
            logger.debug(f'Registering authentication provider for type: {config.auth_type}')
            register_provider_by_type(config.auth_type)
        else:
            logger.debug('No authentication type specified, using none')

        # Check if the requested auth type is available
        if config.auth_type != 'none' and not is_auth_type_available(config.auth_type):
            logger.warning(
                f'Authentication type {config.auth_type} is not available. Falling back to none.'
            )
            config.auth_type = 'none'

        # Get the auth provider
        auth_provider = get_auth_provider(config)

        # Get authentication components
        auth_headers = auth_provider.get_auth_headers()
        # Get auth params (not used directly but may be needed in the future)
        _ = auth_provider.get_auth_params()
        auth_cookies = auth_provider.get_auth_cookies()
        httpx_auth = auth_provider.get_httpx_auth()

        # Helper function to handle authentication configuration errors
        def handle_auth_error(auth_type, error_message):
            """Handle authentication configuration errors.

            Args:
                auth_type: The authentication type
                error_message: The error message to log

            """
            logger.error(
                f'Authentication provider {auth_provider.provider_name} is not properly configured'
            )
            logger.error(error_message)
            logger.error('Server shutting down due to authentication configuration error.')
            sys.exit(1)

        # Check if the provider is properly configured
        if not auth_provider.is_configured() and config.auth_type != 'none':
            if config.auth_type == 'bearer':
                handle_auth_error(
                    'bearer',
                    'Bearer authentication requires a valid token. Please provide a token using --auth-token command line argument or AUTH_TOKEN environment variable.',
                )
            elif config.auth_type == 'basic':
                handle_auth_error(
                    'basic',
                    'Basic authentication requires both username and password. Please provide them using --auth-username and --auth-password command line arguments or AUTH_USERNAME and AUTH_PASSWORD environment variables.',
                )
            elif config.auth_type == 'api_key':
                handle_auth_error(
                    'api_key',
                    'API Key authentication requires a valid API key. Please provide it using --auth-api-key command line argument or AUTH_API_KEY environment variable.',
                )
            elif config.auth_type == 'cognito':
                handle_auth_error(
                    'cognito',
                    'Cognito authentication requires client ID, username, and password. Please provide them using --auth-cognito-client-id, --auth-cognito-username, and --auth-cognito-password command line arguments or corresponding environment variables.',
                )
            else:
                logger.warning(
                    'Continuing with incomplete authentication configuration. This may cause API requests to fail.'
                )

        # Log authentication info
        if config.auth_type != 'none':
            logger.info(f'Using {auth_provider.provider_name} authentication')

        # Create the HTTP client with authentication and connection pooling
        # Use DynamicAuthClient to support per-request Bearer tokens
        from insly.openapi_mcp_server.utils.dynamic_auth_client import create_dynamic_auth_client
        
        client = create_dynamic_auth_client(
            base_url=config.api_base_url,
            default_headers=auth_headers,
            auth=httpx_auth,
            cookies=auth_cookies,
            # Pass through other client configuration from HttpClientFactory
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            follow_redirects=True,
        )
        logger.info(f'Created DynamicAuthClient for API base URL: {config.api_base_url} (supports per-request Bearer tokens)')

        # Update API name from OpenAPI spec title if available
        if openapi_spec and isinstance(openapi_spec, dict) and 'info' in openapi_spec:
            if 'title' in openapi_spec['info'] and openapi_spec['info']['title']:
                config.api_name = openapi_spec['info']['title']
                logger.info(f'Updated API name from OpenAPI spec title: {config.api_name}')

        # Generate meaningful tool names from OpenAPI metadata
        logger.info('Generating tool name mappings from OpenAPI specification')
        try:
            mcp_names = generate_mcp_names(openapi_spec)
            mcp_names = validate_tool_names(mcp_names)
            logger.info(f'Generated {len(mcp_names)} tool name mappings')
        except Exception as e:
            logger.warning(f'Failed to generate tool name mappings: {e}. Using default operationIds.')
            mcp_names = {}

        # Create the FastMCP server using from_openapi
        logger.info('Creating FastMCP server from OpenAPI specification')
        server = FastMCP.from_openapi(
            openapi_spec=openapi_spec,
            client=client,
            name=config.api_name or 'OpenAPI MCP Server',
            mcp_names=mcp_names  # Pass our custom tool name mappings
        )

        logger.info(f'Successfully configured API: {config.api_name}')

        # Enhance tool descriptions with header parameter information
        try:
            logger.info('Enhancing tool descriptions with header parameter information')
            enhance_tool_descriptions(server, openapi_spec)
        except Exception as e:
            logger.warning(f'Failed to enhance tool descriptions: {e}')
            import traceback
            logger.warning(f'Traceback: {traceback.format_exc()}')

        # Generate MCP-compliant prompts
        try:
            logger.info(f'Generating MCP prompts for API: {config.api_name}')
            # Create prompt manager
            prompt_manager = MCPPromptManager()

            # Generate prompts with our custom name mappings
            asyncio.run(prompt_manager.generate_prompts(server, config.api_name, openapi_spec, mcp_names))

            # Register resource handler
            prompt_manager.register_api_resource_handler(server, config.api_name, client)

        except Exception as e:
            logger.warning(f'Failed to generate operation-specific prompts: {e}')
            import traceback

            logger.warning(f'Traceback: {traceback.format_exc()}')

        # Register health check tool
        async def health_check() -> Dict[str, Any]:
            """Check the health of the server and API.

            Returns:
                Dict[str, Any]: Health check results

            """
            api_health = True
            api_message = 'API is reachable'

            # Try to make a simple request to the API
            try:
                # Use the retry-enabled request function
                response = await make_request_with_retry(
                    client=client, method='GET', url='/', max_retries=2, retry_delay=0.5
                )
                status_code = response.status_code
                if status_code >= 400:
                    api_health = False
                    api_message = f'API returned status code {status_code}'
            except Exception as e:
                api_health = False
                api_message = f'Error connecting to API: {str(e)}'

            # Get metrics summary
            summary = metrics.get_summary()

            return {
                'server': {
                    'status': 'healthy',
                    'version': config.version,
                    'uptime': 'N/A',  # Would require tracking start time
                },
                'api': {
                    'name': config.api_name,
                    'status': 'healthy' if api_health else 'unhealthy',
                    'message': api_message,
                    'base_url': config.api_base_url,
                },
                'metrics': summary,
            }

    except Exception as e:
        logger.error(f'Error setting up API: {e}')
        logger.error('Server shutting down due to API setup error.')
        import traceback

        logger.error(f'Traceback: {traceback.format_exc()}')
        sys.exit(1)

    # Move the logging here, after the server is fully initialized
    # Get the actual tools from the server's internal structure
    tool_count = 0
    tool_names = []

    # Try different ways to access tools based on FastMCP implementation
    if hasattr(server, 'list_tools'):
        try:
            # Use asyncio to run the async method in a synchronous context
            tools = asyncio.run(server.list_tools())  # type: ignore
            tool_count = len(tools)
            tool_names = [tool.get('name') for tool in tools]

            # DEBUG - Log detailed information about each tool
            logger.debug(f'Found {tool_count} tools via list_tools()')
            for i, tool in enumerate(tools):
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', 'no description')
                logger.debug(f'Tool {i}: {tool_name} - {tool_desc}')

                # Check if the tool has a schema
                if 'parameters' in tool:
                    params = tool.get('parameters', {})
                    if 'properties' in params:
                        properties = params.get('properties', {})
                        logger.debug(f'  Parameters: {list(properties.keys())}')
        except Exception as e:
            logger.warning(f'Failed to list tools: {e}')
            import traceback

            logger.debug(f'Tool listing error traceback: {traceback.format_exc()}')

    # DEBUG - Try to access tools directly if available
    tools = getattr(server, '_tools', {})
    if tools:
        logger.debug(f'Server has {len(tools)} tools in _tools attribute')
        for tool_name, tool in tools.items():
            logger.debug(f'Direct tool: {tool_name}')

    # Log the prompt count
    prompt_count = (
        len(server._prompt_manager._prompts)
        if hasattr(server, '_prompt_manager') and hasattr(server._prompt_manager, '_prompts')
        else 0
    )

    # Log details of registered components
    if tool_count > 0:
        logger.info(f'Registered tools: {tool_names}')

    if (
        prompt_count > 0
        and hasattr(server, '_prompt_manager')
        and hasattr(server._prompt_manager, '_prompts')
    ):
        prompt_names = list(server._prompt_manager._prompts.keys())
        logger.info(f'Registered prompts: {prompt_names}')

    return server

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    # Store original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)

    def signal_handler(sig, frame):
        """Handle signals by logging metrics then chain to original handler."""
        logger.debug(f'Received signal {sig}, shutting down gracefully...')

        # Log final metrics
        summary = metrics.get_summary()
        logger.info(f'Final metrics: {summary}')

        # if sig is signal.SIGINT handle gracefully
        if sig == signal.SIGINT:
            logger.info('Process Interrupted, Shutting down gracefully...')
            sys.exit(0)

        # For SIGINT, chain to the original handler
        if (
            sig == signal.SIGINT
            and original_sigint != signal.SIG_DFL
            and original_sigint != signal.SIG_IGN
        ):
            # Call the original handler
            if callable(original_sigint):
                original_sigint(sig, frame)

        # For other signals or if no original handler, just return
        # This lets the default handling take over

    # Register for SIGTERM only
    signal.signal(signal.SIGTERM, signal_handler)

    # For SIGINT, we'll use a special handler that logs then chains to original
    signal.signal(signal.SIGINT, signal_handler)

def main():
    """Run the MCP server with CLI argument support."""
    parser = argparse.ArgumentParser(
        description='This project is a server that dynamically creates Model Context Protocol (MCP) tools and resources from OpenAPI specifications. It allows Large Language Models (LLMs) to interact with APIs through the Model Context Protocol.'
    )
    # Server configuration
    parser.add_argument('--port', type=int, help='Port to run the server on')
    parser.add_argument('--sse-port', type=int, help='Port for SSE transport (default: 8001)')
    parser.add_argument('--enable-sse', action='store_true', default=None, help='Enable SSE transport for legacy clients')
    parser.add_argument('--disable-sse', action='store_true', help='Disable SSE transport')
    parser.add_argument('--path', type=str, help='HTTP endpoint path (default: /mcp)')
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level',
    )
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    # API configuration
    parser.add_argument('--api-name', help='Name of the API (default: petstore)')
    parser.add_argument('--api-url', help='Base URL of the API')
    parser.add_argument('--spec-url', help='URL of the OpenAPI specification')
    parser.add_argument('--spec-path', help='Local path to the OpenAPI specification file')

    # Authentication configuration
    parser.add_argument(
        '--auth-type',
        choices=['none', 'basic', 'bearer', 'api_key', 'cognito'],
        help='Authentication type to use (default: none)',
    )

    # Basic auth
    parser.add_argument('--auth-username', help='Username for basic authentication')
    parser.add_argument('--auth-password', help='Password for basic authentication')

    # Bearer auth
    parser.add_argument('--auth-token', help='Token for bearer authentication')

    # API key auth
    parser.add_argument('--auth-api-key', help='API key for API key authentication')
    parser.add_argument('--auth-api-key-name', help='Name of the API key (default: api_key)')
    parser.add_argument(
        '--auth-api-key-in',
        choices=['header', 'query', 'cookie'],
        help='Where to place the API key (default: header)',
    )

    # Cognito auth
    parser.add_argument('--auth-cognito-client-id', help='Client ID for Cognito authentication')
    parser.add_argument('--auth-cognito-username', help='Username for Cognito authentication')
    parser.add_argument('--auth-cognito-password', help='Password for Cognito authentication')
    parser.add_argument(
        '--auth-cognito-user-pool-id', help='User Pool ID for Cognito authentication'
    )
    parser.add_argument('--auth-cognito-region', help='AWS region for Cognito (default: us-east-1)')

    args = parser.parse_args()

    # Set up logging with loguru at specified level
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), level=args.log_level)
    logger.info(f'Starting server with logging level: {args.log_level}')

    # Load configuration
    logger.debug('Loading configuration from arguments and environment')
    config = load_config(args)
    logger.debug(f'Configuration loaded: api_name={config.api_name}, host={config.host}, port={config.port}, path={config.path}')

    # Create and run the MCP server
    logger.info('Creating MCP server')
    mcp_server = create_mcp_server(config)

    # Set up signal handlers
    setup_signal_handlers()

    try:
        # Get counts of prompts, tools, resources, and resource templates
        async def get_all_counts(server):
            prompts = await server.get_prompts()
            tools = await server.get_tools()
            resources = await server.get_resources()

            # Get resource templates if available
            resource_templates = []
            if hasattr(server, 'get_resource_templates'):
                try:
                    resource_templates = await server.get_resource_templates()
                except AttributeError as e:
                    # This is expected if the method exists but is not implemented
                    logger.debug(f'get_resource_templates exists but not implemented: {e}')
                except Exception as e:
                    # Log other unexpected errors
                    logger.warning(f'Error retrieving resource templates: {e}')

            return len(prompts), len(tools), len(resources), len(resource_templates)

        prompt_count, tool_count, resource_count, resource_template_count = asyncio.run(
            get_all_counts(mcp_server)
        )

        # Log all counts in a single statement
        logger.info(
            f'Server components: {prompt_count} prompts, {tool_count} tools, {resource_count} resources, {resource_template_count} resource templates'
        )

        # Check if we have at least one tool or resource
        if tool_count == 0 and resource_count == 0:
            logger.warning(
                'No tools or resources were registered. This might indicate an issue with the API specification or authentication.'
            )
    except Exception as e:
        logger.error(f'Error counting tools and resources: {e}')
        logger.error('Server shutting down due to error in tool/resource registration.')
        import traceback

        logger.error(f'Traceback: {traceback.format_exc()}')
        sys.exit(1)

    # Run server with appropriate transport configuration
    if config.enable_sse:
        # Use multi-transport runner for dual transport support
        from insly.openapi_mcp_server.multi_transport import run_dual_transport
        run_dual_transport(config)
    else:
        # Run single streamable-http transport
        logger.info(f'Starting HTTP server on http://{config.host}:{config.port}{config.path}')
        mcp_server.run(
            transport="streamable-http",
            host=config.host,
            port=config.port,
            path=config.path
        )

if __name__ == '__main__':
    main()
