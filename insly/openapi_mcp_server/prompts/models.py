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

"""Data models for MCP prompts."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional, Union

class PromptArgument(BaseModel):
    """Argument for an MCP prompt."""

    name: str = Field(..., description='Unique identifier for the argument')
    description: Optional[str] = Field(None, description='Human-readable description')
    required: bool = Field(False, description='Whether the argument is required')

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {'name': self.name, 'required': self.required}
        if self.description:
            result['description'] = self.description
        return result

class ResourceContent(BaseModel):
    """Content for a resource message."""

    uri: str = Field(..., description='URI of the resource')
    mimeType: str = Field('application/json', description='MIME type of the resource')
    text: Optional[str] = Field(None, description='Text content of the resource')

class TextMessage(BaseModel):
    """Text message content."""

    type: Literal['text'] = Field('text', description='Type of message content')
    text: str = Field(..., description='Text content')

class ResourceMessage(BaseModel):
    """Resource message content."""

    type: Literal['resource'] = Field('resource', description='Type of message content')
    resource: ResourceContent = Field(..., description='Resource content')

class PromptMessage(BaseModel):
    """Message in an MCP prompt."""

    role: str = Field(..., description='Role of the message sender')
    content: Union[TextMessage, ResourceMessage] = Field(..., description='Content of the message')

class MCPPrompt(BaseModel):
    """MCP-compliant prompt definition."""

    name: str = Field(..., description='Unique identifier for the prompt')
    description: Optional[str] = Field(None, description='Human-readable description')
    arguments: Optional[List[PromptArgument]] = Field(None, description='Arguments for the prompt')
    messages: Optional[List[PromptMessage]] = Field(None, description='Messages in the prompt')
