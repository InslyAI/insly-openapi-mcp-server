#!/usr/bin/env python3
"""Test script to verify Swagger 2.0 support."""

import json
from awslabs.openapi_mcp_server.utils.swagger_converter import convert_swagger_to_openapi, is_swagger_2_spec

# Sample Swagger 2.0 spec (Petstore v2)
swagger2_spec = {
    "swagger": "2.0",
    "info": {
        "version": "1.0.0",
        "title": "Swagger Petstore",
        "description": "A sample API that uses a petstore as an example"
    },
    "host": "petstore.swagger.io",
    "basePath": "/v2",
    "schemes": ["https", "http"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "operationId": "listPets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return at one time",
                        "required": False,
                        "type": "integer",
                        "format": "int32"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A paged array of pets",
                        "schema": {
                            "$ref": "#/definitions/Pets"
                        }
                    }
                }
            },
            "post": {
                "summary": "Create a pet",
                "operationId": "createPets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "description": "Pet to add to the store",
                        "required": True,
                        "schema": {
                            "$ref": "#/definitions/Pet"
                        }
                    }
                ],
                "responses": {
                    "201": {
                        "description": "Null response"
                    }
                }
            }
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Info for a specific pet",
                "operationId": "showPetById",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "The id of the pet to retrieve",
                        "type": "string"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Expected response to a valid request",
                        "schema": {
                            "$ref": "#/definitions/Pet"
                        }
                    }
                }
            }
        }
    },
    "definitions": {
        "Pet": {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {
                    "type": "integer",
                    "format": "int64"
                },
                "name": {
                    "type": "string"
                },
                "tag": {
                    "type": "string"
                }
            }
        },
        "Pets": {
            "type": "array",
            "items": {
                "$ref": "#/definitions/Pet"
            }
        }
    },
    "securityDefinitions": {
        "api_key": {
            "type": "apiKey",
            "name": "api_key",
            "in": "header"
        },
        "petstore_auth": {
            "type": "oauth2",
            "authorizationUrl": "https://petstore.swagger.io/oauth/authorize",
            "flow": "implicit",
            "scopes": {
                "write:pets": "modify pets in your account",
                "read:pets": "read your pets"
            }
        }
    }
}

def test_swagger2_conversion():
    """Test the Swagger 2.0 to OpenAPI 3.0 conversion."""
    print("Testing Swagger 2.0 conversion...")
    
    # Check if it's detected as Swagger 2.0
    assert is_swagger_2_spec(swagger2_spec), "Failed to detect Swagger 2.0 spec"
    print("✓ Correctly detected as Swagger 2.0")
    
    # Convert to OpenAPI 3.0
    openapi_spec = convert_swagger_to_openapi(swagger2_spec)
    
    # Verify conversion
    assert openapi_spec.get('openapi') == '3.0.0', "Missing OpenAPI version"
    print("✓ Converted to OpenAPI 3.0")
    
    # Check servers
    assert 'servers' in openapi_spec, "Missing servers"
    assert len(openapi_spec['servers']) == 2, "Wrong number of servers"
    assert openapi_spec['servers'][0]['url'] == 'https://petstore.swagger.io/v2', "Wrong server URL"
    print("✓ Servers converted correctly")
    
    # Check components
    assert 'components' in openapi_spec, "Missing components"
    assert 'schemas' in openapi_spec['components'], "Missing schemas"
    assert 'Pet' in openapi_spec['components']['schemas'], "Missing Pet schema"
    print("✓ Components structure created")
    
    # Check path conversion
    assert '/pets' in openapi_spec['paths'], "Missing /pets path"
    pet_post = openapi_spec['paths']['/pets']['post']
    assert 'requestBody' in pet_post, "Body parameter not converted to requestBody"
    assert 'parameters' not in pet_post or not any(p.get('in') == 'body' for p in pet_post.get('parameters', [])), "Body parameter not removed from parameters"
    print("✓ Request body converted correctly")
    
    # Check responses
    pet_get = openapi_spec['paths']['/pets']['get']
    assert 'content' in pet_get['responses']['200'], "Response schema not converted to content"
    print("✓ Responses converted correctly")
    
    # Check $ref updates
    ref_path = pet_get['responses']['200']['content']['application/json']['schema']['$ref']
    assert ref_path == '#/components/schemas/Pets', f"Reference not updated: {ref_path}"
    print("✓ References updated correctly")
    
    # Check security schemes
    assert 'securitySchemes' in openapi_spec['components'], "Missing securitySchemes"
    assert 'petstore_auth' in openapi_spec['components']['securitySchemes'], "Missing OAuth2 scheme"
    oauth = openapi_spec['components']['securitySchemes']['petstore_auth']
    assert 'flows' in oauth, "OAuth2 flows not converted"
    assert 'implicit' in oauth['flows'], "OAuth2 implicit flow not converted"
    print("✓ Security definitions converted correctly")
    
    print("\n✅ All tests passed! Swagger 2.0 conversion is working correctly.")
    
    # Pretty print the converted spec
    print("\n" + "="*50)
    print("Converted OpenAPI 3.0 spec:")
    print("="*50)
    print(json.dumps(openapi_spec, indent=2))

if __name__ == "__main__":
    test_swagger2_conversion()