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

"""Enhance tool descriptions with header parameter information."""

from typing import Dict, List, Any, Optional
from insly.openapi_mcp_server import logger

def enhance_description_with_headers(
    base_description: str,
    openapi_spec: Dict[str, Any],
    operation_id: str,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> str:
    """Enhance a tool description with header parameter information.
    
    Args:
        base_description: The original tool description
        openapi_spec: The complete OpenAPI specification
        operation_id: The operation ID to find header parameters for
        path: The path of the operation (used when operation_id is None)
        method: The HTTP method of the operation (used when operation_id is None)
        
    Returns:
        Enhanced description with header parameter documentation
    """
    # Find the operation in the OpenAPI spec
    operation = None
    if operation_id:
        operation = find_operation_by_id(openapi_spec, operation_id)
    
    # If not found by ID or no ID provided, try by path and method
    if not operation and path and method:
        operation = find_operation_by_path_and_method(openapi_spec, path, method)
    
    if not operation:
        return base_description
    
    # Extract header parameters
    header_params = []
    if 'parameters' in operation:
        for param in operation['parameters']:
            if isinstance(param, dict) and param.get('in') == 'header':
                header_params.append(param)
    
    # Extract security requirements
    security_info = extract_security_requirements(openapi_spec, operation)
    
    # If no header params or security, return original description
    if not header_params and not security_info:
        return base_description
    
    # Build enhanced description
    enhanced_parts = [base_description]
    
    # Add security information if present
    if security_info:
        enhanced_parts.append("\n\n**Authentication Required:**")
        enhanced_parts.append(f"\n{security_info}")
    
    # Add header parameters
    if header_params:
        enhanced_parts.append("\n\n**Header Parameters:**")
        for param in header_params:
            name = param.get('name', 'Unknown')
            required = param.get('required', False)
            description = param.get('description', 'No description provided')
            schema = param.get('schema', {})
            
            required_marker = " (Required)" if required else " (Optional)"
            
            # Add type information if available
            param_type = schema.get('type', '')
            if param_type:
                type_info = f" [{param_type}]"
            else:
                type_info = ""
            
            enhanced_parts.append(f"\n- **{name}**{required_marker}{type_info}: {description}")
    
    return ''.join(enhanced_parts)


def find_operation_by_id(openapi_spec: Dict[str, Any], operation_id: str) -> Optional[Dict[str, Any]]:
    """Find an operation in the OpenAPI spec by its operationId.
    
    Args:
        openapi_spec: The OpenAPI specification
        operation_id: The operation ID to find
        
    Returns:
        The operation object if found, None otherwise
    """
    if 'paths' not in openapi_spec:
        return None
    
    for path, path_item in openapi_spec['paths'].items():
        if not isinstance(path_item, dict):
            continue
            
        for method in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
            if method in path_item:
                operation = path_item[method]
                if isinstance(operation, dict) and operation.get('operationId') == operation_id:
                    return operation
    
    return None


def find_operation_by_path_and_method(openapi_spec: Dict[str, Any], path: str, method: str) -> Optional[Dict[str, Any]]:
    """Find an operation in the OpenAPI spec by its path and method.
    
    Args:
        openapi_spec: The OpenAPI specification
        path: The path of the operation (e.g., "/logout")
        method: The HTTP method (e.g., "GET")
        
    Returns:
        The operation object if found, None otherwise
    """
    if 'paths' not in openapi_spec:
        return None
    
    # Normalize method to lowercase
    method_lower = method.lower()
    
    # Try exact path match first
    if path in openapi_spec['paths']:
        path_item = openapi_spec['paths'][path]
        if isinstance(path_item, dict) and method_lower in path_item:
            return path_item[method_lower]
    
    # If not found, try with path parameters replaced
    # Sometimes the spec has {param} but the route has the actual pattern
    for spec_path, path_item in openapi_spec['paths'].items():
        if not isinstance(path_item, dict):
            continue
            
        # Simple pattern matching for path parameters
        # Convert {param} to a regex pattern
        pattern = spec_path
        if '{' in pattern:
            import re
            # Replace {param} with a regex that matches anything except /
            pattern = re.escape(pattern)
            pattern = pattern.replace(r'\{', '{').replace(r'\}', '}')
            pattern = re.sub(r'{[^}]+}', r'[^/]+', pattern)
            pattern = f"^{pattern}$"
            
            if re.match(pattern, path):
                if method_lower in path_item:
                    return path_item[method_lower]
    
    return None


def extract_security_requirements(openapi_spec: Dict[str, Any], operation: Dict[str, Any]) -> Optional[str]:
    """Extract security requirements for an operation.
    
    Args:
        openapi_spec: The complete OpenAPI specification
        operation: The operation object
        
    Returns:
        A human-readable description of security requirements
    """
    # Check operation-level security first
    security = operation.get('security')
    
    # Fall back to global security if not specified at operation level
    if security is None and 'security' in openapi_spec:
        security = openapi_spec['security']
    
    if not security:
        return None
    
    # Get security schemes definitions
    security_schemes = {}
    if 'components' in openapi_spec and 'securitySchemes' in openapi_spec['components']:
        security_schemes = openapi_spec['components']['securitySchemes']
    
    # Build security description
    security_descriptions = []
    
    for security_req in security:
        if not isinstance(security_req, dict):
            continue
            
        for scheme_name, scopes in security_req.items():
            if scheme_name in security_schemes:
                scheme = security_schemes[scheme_name]
                
                if scheme.get('type') == 'http' and scheme.get('scheme') == 'bearer':
                    desc = f"Bearer token authentication required. Include 'Authorization: Bearer <token>' header"
                    if scheme.get('bearerFormat'):
                        desc += f" (Format: {scheme['bearerFormat']})"
                    security_descriptions.append(desc)
                    
                elif scheme.get('type') == 'apiKey':
                    location = scheme.get('in', 'header')
                    name = scheme.get('name', 'Unknown')
                    desc = f"API Key authentication required. Include '{name}' in {location}"
                    security_descriptions.append(desc)
                    
                elif scheme.get('type') == 'http' and scheme.get('scheme') == 'basic':
                    desc = "Basic authentication required. Include 'Authorization: Basic <credentials>' header"
                    security_descriptions.append(desc)
                    
                elif scheme.get('type') == 'oauth2':
                    desc = "OAuth 2.0 authentication required"
                    if scopes:
                        desc += f" with scopes: {', '.join(scopes)}"
                    security_descriptions.append(desc)
    
    if security_descriptions:
        return '\n'.join(f"- {desc}" for desc in security_descriptions)
    
    return None


def enhance_tool_descriptions(server: Any, openapi_spec: Dict[str, Any]) -> None:
    """Enhance all tool descriptions in the server with header parameter information.
    
    Args:
        server: The FastMCP server instance
        openapi_spec: The OpenAPI specification
    """
    if not hasattr(server, '_tool_manager') or not hasattr(server._tool_manager, '_tools'):
        logger.warning("Server does not have tool manager or tools")
        return
    
    tools = server._tool_manager._tools
    enhanced_count = 0
    
    for tool_name, tool in tools.items():
        # Get the operation ID, path, and method from the tool
        operation_id = None
        path = None
        method = None
        
        # Try to get route information from tool
        route = None
        if hasattr(tool, '_route'):
            route = tool._route
        elif hasattr(tool, 'route'):
            route = tool.route
        
        if route:
            # Get operation_id if available
            if hasattr(route, 'operation_id'):
                operation_id = route.operation_id
            
            # Get path and method
            if hasattr(route, 'path'):
                path = route.path
            if hasattr(route, 'method'):
                method = route.method
        
        # Enhance the description
        original_description = tool.description
        enhanced_description = enhance_description_with_headers(
            original_description,
            openapi_spec,
            operation_id,
            path,
            method
        )
        
        if enhanced_description != original_description:
            tool.description = enhanced_description
            enhanced_count += 1
            logger.debug(f"Enhanced description for tool '{tool_name}' (path: {path}, method: {method})")
    
    if enhanced_count > 0:
        logger.info(f"Enhanced {enhanced_count} tool descriptions with header parameter information")