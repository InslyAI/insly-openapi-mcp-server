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

"""Tool naming utilities for generating meaningful MCP tool names from OpenAPI specs."""

import re
from typing import Dict, Any, List, Optional, Set
from insly.openapi_mcp_server import logger


def snake_case(text: str) -> str:
    """Convert text to snake_case.
    
    Args:
        text: Text to convert
        
    Returns:
        str: Snake case version of the text
    """
    # Remove special characters and normalize spaces
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces and hyphens with underscores
    text = re.sub(r'[-\s]+', '_', text)
    # Convert camelCase to snake_case
    text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
    # Convert to lowercase and remove duplicate underscores
    text = re.sub(r'_+', '_', text.lower())
    # Remove leading/trailing underscores
    return text.strip('_')


def extract_resource_from_path(path: str) -> str:
    """Extract the main resource name from an API path.
    
    Args:
        path: API path (e.g., '/api/v1/users/{id}/posts')
        
    Returns:
        str: Extracted resource name (e.g., 'posts')
    """
    # Remove leading slash and split by /
    parts = path.strip('/').split('/')
    
    # Filter out common API prefixes and parameters
    filtered_parts = []
    for part in parts:
        # Skip version indicators, 'api', and path parameters
        if (not part.startswith('v') or not part[1:].isdigit()) and \
           part != 'api' and \
           not (part.startswith('{') and part.endswith('}')):
            filtered_parts.append(part)
    
    # Return the last meaningful part, or the second-to-last if the last is a parameter
    if filtered_parts:
        return filtered_parts[-1]
    
    # Fallback: try to find any non-parameter part
    for part in reversed(parts):
        if not (part.startswith('{') and part.endswith('}')) and part != 'api':
            return part
    
    return 'resource'


def generate_tool_name_from_summary(summary: str) -> Optional[str]:
    """Generate a tool name from an operation summary.
    
    Args:
        summary: Operation summary text
        
    Returns:
        Optional[str]: Generated tool name or None if summary is not suitable
    """
    if not summary or len(summary) > 100:  # Skip very long summaries
        return None
    
    # Convert to snake_case
    name = snake_case(summary)
    
    # Ensure it starts with a verb or is descriptive enough
    common_verbs = ['get', 'list', 'create', 'update', 'delete', 'patch', 'put', 'post', 
                    'fetch', 'retrieve', 'add', 'remove', 'set', 'check', 'validate']
    
    parts = name.split('_')
    if parts and parts[0] in common_verbs:
        return name
    
    # If it doesn't start with a verb but is short and descriptive, use it
    if len(parts) <= 4:
        return name
    
    return None


def generate_tool_name_from_path_and_method(path: str, method: str, tag: Optional[str] = None) -> str:
    """Generate a tool name from path, HTTP method, and optional tag.
    
    Args:
        path: API path
        method: HTTP method
        tag: Optional tag for grouping
        
    Returns:
        str: Generated tool name
    """
    method = method.lower()
    resource = extract_resource_from_path(path)
    resource = snake_case(resource)
    
    # Map HTTP methods to more intuitive verbs
    method_mapping = {
        'get': 'get',
        'post': 'create',
        'put': 'update',
        'patch': 'patch',
        'delete': 'delete',
        'head': 'check',
        'options': 'options'
    }
    
    verb = method_mapping.get(method, method)
    
    # Check if path indicates a list operation
    if method == 'get' and not path.rstrip('/').endswith('}'):
        # Likely a list operation
        verb = 'list'
    
    # Build the name
    if tag:
        tag = snake_case(tag)
        # Avoid redundancy if tag and resource are similar
        if tag != resource and not resource.startswith(tag):
            return f"{tag}_{verb}_{resource}"
    
    return f"{verb}_{resource}"


def generate_mcp_names(openapi_spec: Dict[str, Any]) -> Dict[str, str]:
    """Generate a mapping of operationIds to meaningful MCP tool names.
    
    Args:
        openapi_spec: The OpenAPI specification
        
    Returns:
        Dict[str, str]: Mapping of operationId to generated tool names
    """
    mcp_names = {}
    used_names: Set[str] = set()
    
    # Extract all operations from the spec
    paths = openapi_spec.get('paths', {})
    
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            # Skip non-operation fields
            if method not in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                continue
            
            operation_id = operation.get('operationId')
            if not operation_id:
                continue
            
            # Try to generate name from summary first
            summary = operation.get('summary', '')
            generated_name = generate_tool_name_from_summary(summary)
            
            # If summary didn't work, use path and method
            if not generated_name:
                tags = operation.get('tags', [])
                tag = tags[0] if tags else None
                generated_name = generate_tool_name_from_path_and_method(path, method, tag)
            
            # Ensure uniqueness
            base_name = generated_name
            counter = 1
            while generated_name in used_names:
                generated_name = f"{base_name}_{counter}"
                counter += 1
            
            used_names.add(generated_name)
            mcp_names[operation_id] = generated_name
            
            logger.debug(f"Mapped operationId '{operation_id}' to tool name '{generated_name}'")
    
    logger.info(f"Generated {len(mcp_names)} tool name mappings")
    return mcp_names


def validate_tool_names(mcp_names: Dict[str, str]) -> Dict[str, str]:
    """Validate and clean tool names to ensure they're valid Python identifiers.
    
    Args:
        mcp_names: Mapping of operationId to tool names
        
    Returns:
        Dict[str, str]: Validated mapping
    """
    validated = {}
    
    for operation_id, name in mcp_names.items():
        # Ensure it's a valid Python identifier
        if not name.isidentifier():
            # Clean it up
            name = re.sub(r'[^\w]', '_', name)
            name = re.sub(r'^(\d)', r'op_\1', name)  # Prefix with 'op_' if starts with digit
            name = name.strip('_')
        
        # Ensure it's not empty
        if not name:
            name = f"operation_{operation_id[:8]}"
        
        # Truncate if too long
        if len(name) > 64:
            name = name[:64].rstrip('_')
        
        validated[operation_id] = name
    
    return validated