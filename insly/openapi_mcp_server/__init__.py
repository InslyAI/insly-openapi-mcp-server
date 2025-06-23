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

"""
OpenAPI MCP Server - A server that dynamically creates MCP tools and resources from OpenAPI specifications.
"""

__version__ = '0.1.0'

import inspect
import sys

from loguru import logger

# Remove default loguru handler
logger.remove()

def get_format():
    return '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'

# Set up enhanced logging format to include function name, line number, and logger name
# Fixed the whitespace issue after log level by removing padding
logger.add(
    sys.stdout,
    format=get_format(),
    level='INFO',
)

def get_caller_info():
    """Get information about the caller of a function.

    Returns:
        str: A string containing information about the caller
    """
    # Get the current frame
    current_frame = inspect.currentframe()
    if not current_frame:
        return 'unknown'

    # Go up one frame
    parent_frame = current_frame.f_back
    if not parent_frame:
        return 'unknown'

    # Go up another frame to find the caller
    caller_frame = parent_frame.f_back
    if not caller_frame:
        return 'unknown'

    # Get filename, function name, and line number
    caller_info = inspect.getframeinfo(caller_frame)
    return f'{caller_info.filename}:{caller_info.function}:{caller_info.lineno}'

__all__ = ['__version__', 'logger', 'get_caller_info']
