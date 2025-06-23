# Contributing to insly.ai OpenAPI MCP Server

Thank you for your interest in contributing to the insly.ai OpenAPI MCP Server! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please create an issue on our [GitHub repository](https://github.com/kivilaid/insly-openapi-mcp-server/issues).

### Submitting Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Write or update tests as needed
5. Ensure all tests pass
6. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/kivilaid/insly-openapi-mcp-server.git
cd insly-openapi-mcp-server

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
pyright
```

### Code Style

- We use `ruff` for code formatting and linting
- Follow PEP 8 guidelines
- Add type hints where appropriate
- Write clear, descriptive commit messages

### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for high test coverage

## Questions?

If you have questions, please reach out to us at support@insly.ai

Thank you for contributing!

---

Made with ❤️ by [insly.ai](https://insly.ai)