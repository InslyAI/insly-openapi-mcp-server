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

"""Configuration utilities for the OpenAPI MCP Server."""

import os

# Metrics configuration
METRICS_MAX_HISTORY = int(os.environ.get('METRICS_MAX_HISTORY', '100'))
USE_PROMETHEUS = os.environ.get('ENABLE_PROMETHEUS', 'false').lower() == 'true'
PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', '9090'))

# Operation prompts configuration
ENABLE_OPERATION_PROMPTS = os.environ.get('ENABLE_OPERATION_PROMPTS', 'true').lower() == 'true'

# HTTP client configuration
HTTP_MAX_CONNECTIONS = int(os.environ.get('HTTP_MAX_CONNECTIONS', '100'))
HTTP_MAX_KEEPALIVE = int(os.environ.get('HTTP_MAX_KEEPALIVE', '20'))
USE_TENACITY = os.environ.get('USE_TENACITY', 'true').lower() == 'true'

# Cache configuration
CACHE_MAXSIZE = int(os.environ.get('CACHE_MAXSIZE', '1000'))
CACHE_TTL = int(os.environ.get('CACHE_TTL', '3600'))  # 1 hour default
USE_CACHETOOLS = os.environ.get('USE_CACHETOOLS', 'true').lower() == 'true'
