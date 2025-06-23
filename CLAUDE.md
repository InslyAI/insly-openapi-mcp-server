# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Development Setup
```bash
# Install in development mode
pip install -e .

# Install with all optional dependencies
pip install -e ".[all]"

# Install with test dependencies for running tests
pip install -e ".[test]"
```

### Running the Server Locally
```bash
# Run HTTP server with local changes using uvx (defaults to http://localhost:8000/mcp)
uvx --refresh --from . insly-openapi-mcp-server --spec https://petstore3.swagger.io/api/v3/openapi.json --log-level DEBUG

# Run directly with Python module
python -m insly.openapi_mcp_server --spec https://petstore3.swagger.io/api/v3/openapi.json

# Custom port and path
python -m insly.openapi_mcp_server --port 3000 --path /api/mcp --spec https://api.example.com/openapi.json
```

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=insly

# Run specific test modules
pytest tests/api/
pytest tests/utils/
pytest tests/auth/

# Run a single test file
pytest tests/test_server.py

# Run a single test
pytest tests/test_server.py::test_server_initialization
```

### Code Quality Checks
```bash
# Run ruff linter and formatter
ruff check . --fix
ruff format .

# Run type checking with pyright
pyright

# Run pre-commit hooks
pre-commit run --all-files
```

## High-Level Architecture

### Core Components

1. **FastMCP Server** (`insly/openapi_mcp_server/server.py`)
   - Built on FastMCP framework for Model Context Protocol
   - Uses FastMCP.from_openapi() for automatic tool generation
   - Runs as HTTP server using Streamable HTTP transport
   - Default endpoint: http://localhost:8000/mcp
   - Implements graceful shutdown with configurable timeout

2. **Dynamic Tool Generation**
   - Fetches and validates OpenAPI specifications (JSON/YAML)
   - Automatic Swagger 2.0 to OpenAPI 3.0 conversion
   - FastMCP handles all tool generation automatically
   - Supports file upload parameters in Swagger 2.0

3. **Authentication System** (`insly/openapi_mcp_server/auth/`)
   - Factory pattern for authentication providers
   - Supports: Basic, Bearer Token, API Key, AWS Cognito
   - Each auth type has its own module with specific implementation
   - Authentication is applied to all API calls via HTTP client

4. **Swagger Converter** (`insly/openapi_mcp_server/utils/swagger_converter.py`)
   - Automatic detection of Swagger 2.0 specs
   - Converts to OpenAPI 3.0 format
   - Handles file upload type conversions
   - Preserves all functionality during conversion

5. **Production Features**
   - **Caching**: Abstract cache provider with in-memory implementation
   - **Resilience**: HTTP client with retry logic using tenacity
   - **Observability**: Structured logging with loguru
   - **Configuration**: Environment variables and CLI arguments

### Key Design Patterns

1. **Factory Pattern**: Used for authentication providers to allow easy extension
2. **Provider Pattern**: Abstract providers for cache and metrics with pluggable implementations
3. **Singleton Pattern**: Server instance and configuration management
4. **Async/Await**: Fully async implementation for non-blocking I/O operations

### Configuration Hierarchy
1. Environment variables (highest priority)
2. Command-line arguments
3. Default values (lowest priority)

### Server Architecture
- **HTTP Server**: Uses FastMCP's Streamable HTTP transport
- **Default Configuration**: 
  - Host: 0.0.0.0 (for container compatibility)
  - Port: 8000
  - Path: /mcp
- **Transport**: Streamable HTTP only (optimized for production)

### Testing Strategy
- Comprehensive test coverage with pytest
- Async test support with pytest-asyncio
- Mock external dependencies (HTTP calls, auth providers)
- Test all authentication types and edge cases
- Swagger 2.0 conversion testing

This architecture enables seamless API integration with AI assistants through the Model Context Protocol, providing a bridge between OpenAPI specifications and AI models with minimal configuration required.

---

Made with ❤️ by [insly.ai](https://insly.ai)