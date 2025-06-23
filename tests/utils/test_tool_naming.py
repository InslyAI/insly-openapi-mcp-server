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

"""Tests for tool naming utilities."""

import pytest
from insly.openapi_mcp_server.utils.tool_naming import (
    snake_case,
    extract_resource_from_path,
    generate_tool_name_from_summary,
    generate_tool_name_from_path_and_method,
    generate_mcp_names,
    validate_tool_names
)


class TestSnakeCase:
    """Test snake_case conversion."""
    
    @pytest.mark.parametrize("input_text,expected", [
        ("Get tenant features", "get_tenant_features"),
        ("Create a new product", "create_a_new_product"),
        ("getUserByID", "get_user_by_id"),
        ("list-all-users", "list_all_users"),
        ("HTTPSConnection", "https_connection"),
        ("__special__case__", "special_case"),
        ("", ""),
        ("123StartWithNumber", "123_start_with_number"),
    ])
    def test_snake_case_conversion(self, input_text, expected):
        """Test various snake_case conversions."""
        assert snake_case(input_text) == expected


class TestExtractResource:
    """Test resource extraction from paths."""
    
    @pytest.mark.parametrize("path,expected", [
        ("/api/v1/sites/features/{tenantTag}", "features"),
        ("/api/v1/sites/products/{tenantTag}", "products"),
        ("/api/v1/sites/claim-features/{id}", "claim-features"),
        ("/users/{id}/posts", "posts"),
        ("/v2/api/customers", "customers"),
        ("/api/{version}/users", "users"),
        ("/{id}", "resource"),  # Fallback case
        ("/", "resource"),  # Edge case
    ])
    def test_extract_resource_from_path(self, path, expected):
        """Test resource extraction from various paths."""
        assert extract_resource_from_path(path) == expected


class TestGenerateFromSummary:
    """Test tool name generation from summaries."""
    
    def test_valid_summaries(self):
        """Test generation from valid summaries."""
        assert generate_tool_name_from_summary("Get user details") == "get_user_details"
        assert generate_tool_name_from_summary("List all products") == "list_all_products"
        assert generate_tool_name_from_summary("Update customer") == "update_customer"
    
    def test_non_verb_summaries(self):
        """Test summaries that don't start with verbs."""
        assert generate_tool_name_from_summary("User details") == "user_details"
        assert generate_tool_name_from_summary("Product list") == "product_list"
    
    def test_invalid_summaries(self):
        """Test invalid summaries."""
        assert generate_tool_name_from_summary("") is None
        assert generate_tool_name_from_summary("a" * 101) is None  # Too long
        assert generate_tool_name_from_summary("This is a very long summary that exceeds four parts when converted") is None


class TestGenerateFromPathAndMethod:
    """Test tool name generation from path and method."""
    
    def test_basic_generation(self):
        """Test basic path/method generation."""
        assert generate_tool_name_from_path_and_method("/users", "get") == "list_users"
        assert generate_tool_name_from_path_and_method("/users/{id}", "get") == "get_users"
        assert generate_tool_name_from_path_and_method("/users", "post") == "create_users"
        assert generate_tool_name_from_path_and_method("/users/{id}", "put") == "update_users"
        assert generate_tool_name_from_path_and_method("/users/{id}", "delete") == "delete_users"
    
    def test_with_tags(self):
        """Test generation with tags."""
        assert generate_tool_name_from_path_and_method("/products", "get", "Shop") == "shop_list_products"
        assert generate_tool_name_from_path_and_method("/orders", "post", "Shop") == "shop_create_orders"
        # Test redundancy avoidance
        assert generate_tool_name_from_path_and_method("/products", "get", "Products") == "list_products"


class TestGenerateMcpNames:
    """Test full MCP name generation."""
    
    def test_complete_spec(self):
        """Test generation from a complete OpenAPI spec."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "abc123",
                        "summary": "List all users"
                    },
                    "post": {
                        "operationId": "def456",
                        "summary": "Create user"
                    }
                },
                "/users/{id}": {
                    "get": {
                        "operationId": "ghi789",
                        "summary": "Get user by ID",
                        "tags": ["Users"]
                    }
                }
            }
        }
        
        result = generate_mcp_names(spec)
        
        assert result["abc123"] == "list_all_users"
        assert result["def456"] == "create_user"
        assert result["ghi789"] == "get_user_by_id"
    
    def test_hash_operation_ids(self):
        """Test with hash-like operation IDs."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/api/v1/sites/features/{tenantTag}": {
                    "get": {
                        "operationId": "2dedbfd907f6ce906291347459087311",
                        "summary": "Get tenant features",
                        "tags": ["Tenant features"]
                    }
                }
            }
        }
        
        result = generate_mcp_names(spec)
        assert result["2dedbfd907f6ce906291347459087311"] == "get_tenant_features"
    
    def test_duplicate_handling(self):
        """Test handling of duplicate names."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "op1",
                        "summary": "Get users"
                    }
                },
                "/customers": {
                    "get": {
                        "operationId": "op2",
                        "summary": "Get users"  # Same summary
                    }
                }
            }
        }
        
        result = generate_mcp_names(spec)
        assert result["op1"] == "get_users"
        assert result["op2"] == "get_users_1"  # Duplicate handled
    
    def test_missing_operation_id(self):
        """Test operations without operationId."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users"
                    }
                }
            }
        }
        
        result = generate_mcp_names(spec)
        assert len(result) == 0  # No operationId, no mapping


class TestValidateToolNames:
    """Test tool name validation."""
    
    def test_valid_names(self):
        """Test already valid names pass through."""
        names = {
            "op1": "get_users",
            "op2": "create_product"
        }
        result = validate_tool_names(names)
        assert result == names
    
    def test_invalid_characters(self):
        """Test cleaning of invalid characters."""
        names = {
            "op1": "get-users",
            "op2": "create.product",
            "op3": "delete user"
        }
        result = validate_tool_names(names)
        assert result["op1"] == "get_users"
        assert result["op2"] == "create_product"
        assert result["op3"] == "delete_user"
    
    def test_numeric_start(self):
        """Test handling of names starting with numbers."""
        names = {
            "op1": "123_get_users",
            "op2": "456"
        }
        result = validate_tool_names(names)
        assert result["op1"] == "op_123_get_users"
        assert result["op2"] == "op_456"
    
    def test_empty_names(self):
        """Test handling of empty names."""
        names = {
            "op123": "",
            "op456": "___"
        }
        result = validate_tool_names(names)
        assert result["op123"] == "operation_op123"
        assert result["op456"] == "operation_op456"
    
    def test_long_names(self):
        """Test truncation of long names."""
        long_name = "a" * 100
        names = {"op1": long_name}
        result = validate_tool_names(names)
        assert len(result["op1"]) == 64
        assert result["op1"] == "a" * 64