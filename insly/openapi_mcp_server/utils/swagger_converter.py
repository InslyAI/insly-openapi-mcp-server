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

"""Swagger 2.0 to OpenAPI 3.0 converter utilities."""

import copy
import re
from insly.openapi_mcp_server import logger
from typing import Any, Dict, List, Optional, Union

def is_swagger_2_spec(spec: Dict[str, Any]) -> bool:
    """Check if the specification is Swagger 2.0.
    
    Args:
        spec: The API specification
        
    Returns:
        bool: True if it's Swagger 2.0, False otherwise
    """
    return spec.get('swagger') == '2.0'

def convert_swagger_to_openapi(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Swagger 2.0 specification to OpenAPI 3.0.
    
    This is a minimal converter that transforms just enough to make FastMCP happy.
    It focuses on the essential structural differences between the formats.
    
    Args:
        spec: Swagger 2.0 specification
        
    Returns:
        Dict[str, Any]: OpenAPI 3.0 specification
    """
    if not is_swagger_2_spec(spec):
        # Not a Swagger 2.0 spec, return as-is
        return spec
    
    logger.info('Converting Swagger 2.0 specification to OpenAPI 3.0')
    
    try:
        # Deep copy to avoid modifying original
        swagger_spec = copy.deepcopy(spec)
        
        # Create OpenAPI 3.0 structure
        openapi_spec = {
            'openapi': '3.0.0',
            'info': swagger_spec.get('info', {}),
            'paths': {},
            'components': {}
        }
        
        # Convert servers
        if 'host' in swagger_spec:
            schemes = swagger_spec.get('schemes', ['https'])
            base_path = swagger_spec.get('basePath', '')
            openapi_spec['servers'] = [
                {'url': f"{scheme}://{swagger_spec['host']}{base_path}"} 
                for scheme in schemes
            ]
            logger.debug(f"Converted servers: {openapi_spec['servers']}")
        
        # Move reusable components
        components = openapi_spec['components']
        
        # Move definitions to components/schemas
        if 'definitions' in swagger_spec:
            components['schemas'] = swagger_spec['definitions']
            logger.debug(f"Moved {len(components['schemas'])} schemas to components")
        
        # Move parameters to components/parameters
        if 'parameters' in swagger_spec:
            components['parameters'] = swagger_spec['parameters']
        
        # Move responses to components/responses
        if 'responses' in swagger_spec:
            components['responses'] = swagger_spec['responses']
        
        # Convert security definitions
        if 'securityDefinitions' in swagger_spec:
            components['securitySchemes'] = convert_security_definitions(
                swagger_spec['securityDefinitions']
            )
            logger.debug(f"Converted {len(components['securitySchemes'])} security schemes")
        
        # Convert paths
        if 'paths' in swagger_spec:
            openapi_spec['paths'] = convert_paths(swagger_spec['paths'])
            logger.debug(f"Converted {len(openapi_spec['paths'])} paths")
        
        # Copy security requirements
        if 'security' in swagger_spec:
            openapi_spec['security'] = swagger_spec['security']
        
        # Copy tags
        if 'tags' in swagger_spec:
            openapi_spec['tags'] = swagger_spec['tags']
        
        # Copy external docs
        if 'externalDocs' in swagger_spec:
            openapi_spec['externalDocs'] = swagger_spec['externalDocs']
        
        # Update all $ref paths in the entire spec
        openapi_spec = update_refs(openapi_spec)
        
        logger.info('Successfully converted Swagger 2.0 to OpenAPI 3.0')
        return openapi_spec
        
    except Exception as e:
        logger.error(f'Error converting Swagger 2.0 to OpenAPI 3.0: {e}')
        logger.warning('Returning original specification')
        return spec

def convert_security_definitions(security_defs: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Swagger 2.0 security definitions to OpenAPI 3.0 security schemes.
    
    Args:
        security_defs: Swagger 2.0 securityDefinitions
        
    Returns:
        Dict[str, Any]: OpenAPI 3.0 securitySchemes
    """
    security_schemes = {}
    
    for name, definition in security_defs.items():
        scheme = copy.deepcopy(definition)
        
        # Convert type names
        if scheme.get('type') == 'basic':
            scheme['type'] = 'http'
            scheme['scheme'] = 'basic'
        elif scheme.get('type') == 'apiKey' and name.lower() in ['bearer', 'bearertoken', 'bearer_token']:
            # Special case: Bearer tokens are often defined as apiKey in Swagger 2.0
            # but should be http/bearer in OpenAPI 3.0
            if scheme.get('name') == 'Authorization' and scheme.get('in') == 'header':
                scheme['type'] = 'http'
                scheme['scheme'] = 'bearer'
                # Try to extract bearer format from description
                if 'description' in scheme and 'JWT' in scheme['description'].upper():
                    scheme['bearerFormat'] = 'JWT'
                # Remove apiKey specific fields
                scheme.pop('name', None)
                scheme.pop('in', None)
        elif scheme.get('type') == 'oauth2':
            # OAuth2 has significant structural changes
            flows = {}
            if 'flow' in scheme:
                flow_type = scheme['flow']
                flow_data = {
                    'authorizationUrl': scheme.get('authorizationUrl', ''),
                    'tokenUrl': scheme.get('tokenUrl', ''),
                    'scopes': scheme.get('scopes', {})
                }
                
                # Map flow types
                if flow_type == 'implicit':
                    flows['implicit'] = flow_data
                elif flow_type == 'password':
                    flows['password'] = flow_data
                elif flow_type == 'application':
                    flows['clientCredentials'] = flow_data
                elif flow_type == 'accessCode':
                    flows['authorizationCode'] = flow_data
                
                scheme['flows'] = flows
                # Remove old fields
                for field in ['flow', 'authorizationUrl', 'tokenUrl', 'scopes']:
                    scheme.pop(field, None)
        
        security_schemes[name] = scheme
    
    return security_schemes

def convert_paths(paths: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Swagger 2.0 paths to OpenAPI 3.0 format.
    
    Args:
        paths: Swagger 2.0 paths object
        
    Returns:
        Dict[str, Any]: OpenAPI 3.0 paths object
    """
    converted_paths = {}
    
    for path, path_item in paths.items():
        converted_path = {}
        
        for method, operation in path_item.items():
            if method.lower() in ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']:
                converted_path[method] = convert_operation(operation)
            else:
                # Copy other fields like parameters
                converted_path[method] = operation
        
        converted_paths[path] = converted_path
    
    return converted_paths

def convert_operation(operation: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single operation from Swagger 2.0 to OpenAPI 3.0.
    
    Args:
        operation: Swagger 2.0 operation object
        
    Returns:
        Dict[str, Any]: OpenAPI 3.0 operation object
    """
    converted = copy.deepcopy(operation)
    
    # Convert parameters
    if 'parameters' in converted:
        body_params = []
        form_params = []
        other_params = []
        
        for param in converted['parameters']:
            if param.get('in') == 'body':
                body_params.append(param)
            elif param.get('in') == 'formData':
                form_params.append(param)
            else:
                other_params.append(param)
        
        # Handle body parameters
        if body_params:
            # In OpenAPI 3.0, body becomes requestBody
            body_param = body_params[0]  # There should only be one
            converted['requestBody'] = {
                'description': body_param.get('description', ''),
                'required': body_param.get('required', False),
                'content': {
                    'application/json': {
                        'schema': body_param.get('schema', {})
                    }
                }
            }
            
            # Add other content types if consumes is specified
            if 'consumes' in converted:
                for media_type in converted['consumes']:
                    if media_type not in converted['requestBody']['content']:
                        converted['requestBody']['content'][media_type] = {
                            'schema': body_param.get('schema', {})
                        }
        
        # Handle form parameters
        if form_params:
            schema_properties = {}
            required = []
            
            for param in form_params:
                param_type = param.get('type', 'string')
                
                # Convert file type to string with binary format
                if param_type == 'file':
                    param_schema = {
                        'type': 'string',
                        'format': 'binary'
                    }
                else:
                    param_schema = {
                        'type': param_type
                    }
                    if 'format' in param:
                        param_schema['format'] = param['format']
                
                if 'description' in param:
                    param_schema['description'] = param['description']
                
                schema_properties[param['name']] = param_schema
                
                if param.get('required', False):
                    required.append(param['name'])
            
            form_schema = {
                'type': 'object',
                'properties': schema_properties
            }
            if required:
                form_schema['required'] = required
            
            converted['requestBody'] = {
                'content': {
                    'application/x-www-form-urlencoded': {
                        'schema': form_schema
                    }
                }
            }
        
        # Keep only non-body/formData parameters
        if other_params:
            converted['parameters'] = other_params
        else:
            converted.pop('parameters', None)
    
    # Convert responses
    if 'responses' in converted:
        converted_responses = {}
        
        for status_code, response in converted['responses'].items():
            converted_response = copy.deepcopy(response)
            
            # Convert schema to content
            if 'schema' in converted_response:
                schema = converted_response.pop('schema')
                converted_response['content'] = {
                    'application/json': {
                        'schema': schema
                    }
                }
                
                # Add other content types if produces is specified
                if 'produces' in converted:
                    for media_type in converted['produces']:
                        if media_type not in converted_response['content']:
                            converted_response['content'][media_type] = {
                                'schema': schema
                            }
            
            converted_responses[status_code] = converted_response
        
        converted['responses'] = converted_responses
    
    # Remove consumes and produces (now handled in content)
    converted.pop('consumes', None)
    converted.pop('produces', None)
    
    # Note: Security, operationId, tags, summary, description, etc. are preserved
    # as they have the same format in OpenAPI 3.0
    
    return converted

def update_refs(obj: Any, parent_key: Optional[str] = None) -> Any:
    """Recursively update $ref paths from Swagger 2.0 to OpenAPI 3.0 format.
    
    Also converts 'type: file' to 'type: string' with 'format: binary'.
    
    Args:
        obj: The object to update (dict, list, or primitive)
        parent_key: The parent key (used for context)
        
    Returns:
        Any: The updated object
    """
    if isinstance(obj, dict):
        updated = {}
        
        # Check if this is a schema object with type: file
        if obj.get('type') == 'file':
            # Convert file type to string with binary format
            updated['type'] = 'string'
            updated['format'] = 'binary'
            # Copy other properties except 'type'
            for key, value in obj.items():
                if key != 'type':
                    updated[key] = update_refs(value, key)
        else:
            # Normal processing
            for key, value in obj.items():
                if key == '$ref' and isinstance(value, str):
                    # Update reference paths
                    updated[key] = update_ref_path(value)
                else:
                    updated[key] = update_refs(value, key)
        return updated
    elif isinstance(obj, list):
        return [update_refs(item, parent_key) for item in obj]
    else:
        return obj

def update_ref_path(ref: str) -> str:
    """Update a single $ref path from Swagger 2.0 to OpenAPI 3.0 format.
    
    Args:
        ref: The reference path
        
    Returns:
        str: The updated reference path
    """
    # Map of Swagger 2.0 paths to OpenAPI 3.0 paths
    ref_mappings = {
        '#/definitions/': '#/components/schemas/',
        '#/parameters/': '#/components/parameters/',
        '#/responses/': '#/components/responses/',
    }
    
    for old_path, new_path in ref_mappings.items():
        if ref.startswith(old_path):
            return ref.replace(old_path, new_path, 1)
    
    return ref