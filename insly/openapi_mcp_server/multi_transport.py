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

"""Multi-transport support for running both streamable-http and SSE transports."""

import multiprocessing
import signal
import sys
from typing import Optional

from insly.openapi_mcp_server import logger
from insly.openapi_mcp_server.api.config import Config
from insly.openapi_mcp_server.server import create_mcp_server


def run_sse_server(config: Config) -> None:
    """Run SSE transport server on separate port.
    
    Args:
        config: Server configuration
    """
    try:
        logger.info(f'Starting SSE server on http://{config.host}:{config.sse_port}')
        server = create_mcp_server(config)
        server.run(transport="sse", host=config.host, port=config.sse_port)
    except Exception as e:
        logger.error(f'SSE server error: {e}')
        sys.exit(1)


def run_dual_transport(config: Config) -> None:
    """Run both streamable-http and SSE transports.
    
    Args:
        config: Server configuration
    """
    sse_process: Optional[multiprocessing.Process] = None
    
    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully."""
        logger.info('Shutting down multi-transport server...')
        if sse_process and sse_process.is_alive():
            sse_process.terminate()
            sse_process.join(timeout=5)
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if config.enable_sse:
            logger.info('Starting dual transport mode (streamable-http + SSE)')
            
            # Start SSE server in separate process
            sse_process = multiprocessing.Process(
                target=run_sse_server,
                args=(config,),
                name='mcp-sse-server'
            )
            sse_process.start()
            logger.info(f'SSE server process started (PID: {sse_process.pid})')
        else:
            logger.info('SSE transport disabled, running streamable-http only')
        
        # Run main streamable-http server in main process
        logger.info(f'Starting streamable-http server on http://{config.host}:{config.port}{config.path}')
        server = create_mcp_server(config)
        server.run(
            transport="streamable-http",
            host=config.host,
            port=config.port,
            path=config.path
        )
        
    except KeyboardInterrupt:
        logger.info('Received keyboard interrupt')
    except Exception as e:
        logger.error(f'Multi-transport server error: {e}')
    finally:
        # Clean up SSE process if running
        if sse_process and sse_process.is_alive():
            logger.info('Terminating SSE server process...')
            sse_process.terminate()
            sse_process.join(timeout=5)
            if sse_process.is_alive():
                logger.warning('SSE server did not terminate gracefully, forcing...')
                sse_process.kill()