# insly.ai OpenAPI MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Version](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)

A production-ready Model Context Protocol (MCP) server that provides seamless integration with any OpenAPI-compliant API. Built by [insly.ai](https://insly.ai), this server enables AI assistants to interact with your APIs through a standardized protocol.

## 🚀 Features

- **OpenAPI 3.0+ Support**: Full compatibility with OpenAPI 3.0 specifications
- **Swagger 2.0 Support**: Automatic conversion of Swagger 2.0 specs to OpenAPI 3.0
- **Streamable HTTP Transport**: Modern, efficient transport protocol for real-time communication
- **Multiple Authentication Methods**: Support for API Key, Bearer Token, Basic Auth, and AWS Cognito
- **Intelligent Caching**: Built-in caching for improved performance
- **Error Handling**: Robust error handling with detailed logging
- **Production Ready**: Battle-tested and optimized for production environments

## 📋 Requirements

- Python 3.10 or higher
- FastMCP 2.3.0+
- Valid OpenAPI specification (URL or local file)

## 🛠️ Installation

### Using pip

```bash
pip install insly-openapi-mcp-server
```

### Using uvx (Recommended)

```bash
uvx insly-openapi-mcp-server --spec https://api.example.com/openapi.json
```

### From source

```bash
git clone https://github.com/kivilaid/insly-openapi-mcp-server.git
cd insly-openapi-mcp-server
pip install -e .
```

## 🚦 Quick Start

### 1. Basic Usage

Run the server with an OpenAPI specification URL:

```bash
uvx insly-openapi-mcp-server --spec https://api.example.com/openapi.json
```

Or with a local file:

```bash
uvx insly-openapi-mcp-server --spec ./openapi.yaml
```

### 2. With Authentication

#### API Key Authentication
```bash
uvx insly-openapi-mcp-server \
  --spec https://api.example.com/openapi.json \
  --api-key your-api-key
```

#### Bearer Token
```bash
uvx insly-openapi-mcp-server \
  --spec https://api.example.com/openapi.json \
  --bearer-token your-bearer-token
```

#### Basic Authentication
```bash
uvx insly-openapi-mcp-server \
  --spec https://api.example.com/openapi.json \
  --username your-username \
  --password your-password
```

### 3. Configuration Options

```bash
uvx insly-openapi-mcp-server \
  --spec https://api.example.com/openapi.json \
  --port 8080 \                    # Custom port (default: 8000)
  --host 0.0.0.0 \                 # Bind address (default: 0.0.0.0)
  --path /custom-mcp \             # Custom endpoint path (default: /mcp)
  --base-url https://api.example.com \  # Override base URL
  --timeout 30                     # Request timeout in seconds
```

## 🔧 Configuration

### Environment Variables

You can configure the server using environment variables:

```bash
# Server configuration
export SERVER_PORT=8080
export SERVER_HOST=0.0.0.0
export SERVER_PATH=/mcp

# API configuration
export OPENAPI_SPEC_URL=https://api.example.com/openapi.json
export API_BASE_URL=https://api.example.com
export API_TIMEOUT=30

# Authentication
export API_KEY=your-api-key
export BEARER_TOKEN=your-bearer-token
export USERNAME=your-username
export PASSWORD=your-password

# AWS Cognito (if using)
export COGNITO_CLIENT_ID=your-client-id
export COGNITO_CLIENT_SECRET=your-client-secret
export COGNITO_REGION=us-east-1
```

### Configuration File

Create a `.env` file in your working directory:

```env
OPENAPI_SPEC_URL=https://api.example.com/openapi.json
API_KEY=your-api-key
SERVER_PORT=8080
API_TIMEOUT=60
```

## 🔌 MCP Client Integration

### Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "my-api": {
      "command": "uvx",
      "args": [
        "insly-openapi-mcp-server",
        "--spec", "https://api.example.com/openapi.json",
        "--api-key", "your-api-key"
      ]
    }
  }
}
```

### MCP Inspector

Test your server with MCP Inspector:

```bash
# Start the server
uvx insly-openapi-mcp-server --spec https://api.example.com/openapi.json

# In another terminal, run MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

## 📚 Advanced Usage

### Swagger 2.0 Support

The server automatically detects and converts Swagger 2.0 specifications:

```bash
uvx insly-openapi-mcp-server --spec https://api.example.com/swagger.json
```

### Custom Base URL

Override the base URL from the OpenAPI spec:

```bash
uvx insly-openapi-mcp-server \
  --spec ./local-openapi.json \
  --base-url https://production.api.com
```

### Multiple Authentication Headers

Combine different authentication methods:

```bash
uvx insly-openapi-mcp-server \
  --spec https://api.example.com/openapi.json \
  --header "X-Custom-Header: value" \
  --header "X-Another-Header: another-value" \
  --api-key your-api-key
```

## 🐳 Docker Support

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN pip install insly-openapi-mcp-server

CMD ["insly-openapi-mcp-server", "--spec", "${OPENAPI_SPEC_URL}"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  mcp-server:
    image: python:3.10-slim
    command: |
      bash -c "pip install insly-openapi-mcp-server && 
               insly-openapi-mcp-server --spec ${OPENAPI_SPEC_URL}"
    environment:
      - OPENAPI_SPEC_URL=https://api.example.com/openapi.json
      - API_KEY=your-api-key
      - SERVER_PORT=8000
    ports:
      - "8000:8000"
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection refused**
   - Ensure the server is running on the correct port
   - Check firewall settings
   - Verify the host binding (use `0.0.0.0` for Docker)

2. **Authentication errors**
   - Double-check your API credentials
   - Ensure authentication headers are properly formatted
   - Check if the API requires additional headers

3. **Invalid OpenAPI spec**
   - Validate your OpenAPI spec using online validators
   - Ensure the spec URL is accessible
   - Check for CORS issues if accessing from a browser

### Debug Mode

Enable detailed logging:

```bash
uvx insly-openapi-mcp-server \
  --spec https://api.example.com/openapi.json \
  --debug
```

## 🛡️ Security

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Use environment variables for sensitive data
- **HTTPS**: Always use HTTPS for production APIs
- **Rate Limiting**: The server respects API rate limits automatically

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/) specification
- Developed by the team at [insly.ai](https://insly.ai)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/kivilaid/insly-openapi-mcp-server/issues)
- **Email**: support@insly.ai
- **Website**: [insly.ai](https://insly.ai)

---

Made with ❤️ by [insly.ai](https://insly.ai)