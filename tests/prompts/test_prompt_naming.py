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

"""Tests for prompt naming improvements."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from insly.openapi_mcp_server.prompts.generators.operation_prompts import (
    generate_operation_documentation,
    create_operation_prompt
)
from insly.openapi_mcp_server.prompts.prompt_manager import MCPPromptManager


class TestPromptDocumentation:
    """Test prompt documentation generation with friendly names."""
    
    def test_documentation_with_friendly_name(self):
        """Test documentation uses friendly name in title."""
        doc = generate_operation_documentation(
            operation_id="abc123",
            friendly_name="get_users",
            method="get",
            path="/users",
            summary="List all users",
            description="Returns a list of all users",
            parameters=[],
            request_body=None,
            responses={"200": {"description": "Success"}},
            security=None
        )
        
        # Should use friendly name converted to title case
        assert doc.startswith("# Get Users")
        assert "List all users" in doc
    
    def test_documentation_without_friendly_name(self):
        """Test documentation falls back to summary when no friendly name."""
        doc = generate_operation_documentation(
            operation_id="abc123",
            friendly_name=None,
            method="get",
            path="/users",
            summary="List all users",
            description="Returns a list of all users",
            parameters=[],
            request_body=None,
            responses={"200": {"description": "Success"}},
            security=None
        )
        
        # Should use summary as title
        assert doc.startswith("# List all users")
    
    def test_documentation_title_formatting(self):
        """Test various friendly name formats are converted properly."""
        test_cases = [
            ("get_tenant_features", "# Get Tenant Features"),
            ("create_product", "# Create Product"),
            ("update_user_profile", "# Update User Profile"),
            ("delete_claim", "# Delete Claim"),
            ("list_all_items", "# List All Items")
        ]
        
        for friendly_name, expected_title in test_cases:
            doc = generate_operation_documentation(
                operation_id="test",
                friendly_name=friendly_name,
                method="post",
                path="/test",
                summary="",
                description="",
                parameters=[],
                request_body=None,
                responses={},
                security=None
            )
            assert doc.startswith(expected_title)


class TestPromptCreation:
    """Test prompt creation with friendly names."""
    
    @patch('insly.openapi_mcp_server.prompts.generators.operation_prompts.Prompt')
    def test_prompt_name_with_friendly_name(self, mock_prompt_class):
        """Test prompt uses friendly name with _prompt suffix."""
        # Create mock server and prompt
        mock_server = Mock()
        mock_prompt_manager = Mock()
        mock_server._prompt_manager = mock_prompt_manager
        
        # Mock the Prompt.from_function to capture arguments
        mock_prompt = Mock()
        mock_prompt_class.from_function.return_value = mock_prompt
        
        # Create prompt with friendly name
        success = create_operation_prompt(
            server=mock_server,
            api_name="Test API",
            operation_id="abc123",
            friendly_name="get_users",
            method="get",
            path="/users",
            summary="List all users",
            description="",
            parameters=[],
            request_body=None,
            responses={},
            security=None,
            paths={}
        )
        
        # Check that Prompt.from_function was called with correct name
        mock_prompt_class.from_function.assert_called_once()
        call_args = mock_prompt_class.from_function.call_args[1]
        assert call_args['name'] == 'get_users_prompt'
        assert call_args['description'] == 'List all users'
    
    @patch('insly.openapi_mcp_server.prompts.generators.operation_prompts.Prompt')
    def test_prompt_name_without_friendly_name(self, mock_prompt_class):
        """Test prompt falls back to operationId when no friendly name."""
        # Create mock server and prompt
        mock_server = Mock()
        mock_prompt_manager = Mock()
        mock_server._prompt_manager = mock_prompt_manager
        
        # Mock the Prompt.from_function to capture arguments
        mock_prompt = Mock()
        mock_prompt_class.from_function.return_value = mock_prompt
        
        # Create prompt without friendly name
        success = create_operation_prompt(
            server=mock_server,
            api_name="Test API",
            operation_id="abc123",
            friendly_name=None,  # No friendly name
            method="get",
            path="/users",
            summary="List all users",
            description="",
            parameters=[],
            request_body=None,
            responses={},
            security=None,
            paths={}
        )
        
        # Check that Prompt.from_function was called with operationId
        mock_prompt_class.from_function.assert_called_once()
        call_args = mock_prompt_class.from_function.call_args[1]
        assert call_args['name'] == 'abc123'  # Falls back to operationId


class TestPromptManagerIntegration:
    """Test prompt manager integration with friendly names."""
    
    @pytest.mark.asyncio
    async def test_generate_prompts_with_mcp_names(self):
        """Test prompt generation passes friendly names correctly."""
        manager = MCPPromptManager()
        
        # Create mock server
        mock_server = Mock()
        mock_prompt_manager = Mock()
        mock_server._prompt_manager = mock_prompt_manager
        
        # OpenAPI spec with hash-like operationIds
        openapi_spec = {
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "abc123hash",
                        "summary": "List users"
                    }
                }
            }
        }
        
        # Mapping of operationIds to friendly names
        mcp_names = {
            "abc123hash": "list_users"
        }
        
        # Mock create_operation_prompt to verify it receives friendly name
        with patch('insly.openapi_mcp_server.prompts.prompt_manager.create_operation_prompt') as mock_create:
            mock_create.return_value = True
            
            # Generate prompts
            result = await manager.generate_prompts(
                server=mock_server,
                api_name="Test API",
                openapi_spec=openapi_spec,
                mcp_names=mcp_names
            )
            
            # Verify create_operation_prompt was called with friendly name
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['operation_id'] == 'abc123hash'
            assert call_args['friendly_name'] == 'list_users'