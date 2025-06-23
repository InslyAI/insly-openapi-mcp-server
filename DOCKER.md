# Docker Deployment Guide

This guide explains how to deploy the OpenAPI MCP Server using Docker.

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t openapi-mcp-server .

# Run with environment variables
docker run -p 8000:8000 \
  -e API_SPEC_URL="https://petstore3.swagger.io/api/v3/openapi.json" \
  -e API_BASE_URL="https://petstore3.swagger.io/api/v3" \
  openapi-mcp-server
```

### Using Docker Compose

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your API details
nano .env  # or use your favorite editor

# Start the server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_SPEC_URL` | URL of the OpenAPI specification | `https://api.example.com/openapi.json` |
| `API_BASE_URL` | Base URL of the API | `https://api.example.com` |

**Note**: You can use `API_SPEC_PATH` instead of `API_SPEC_URL` for local files.

### Optional Variables

#### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_NAME` | Name of the API | Extracted from OpenAPI spec |
| `API_SPEC_PATH` | Path to local OpenAPI spec file | - |

#### Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_HOST` | Host to bind to | `0.0.0.0` |
| `SERVER_PORT` | Port to listen on | `8000` |
| `SERVER_PATH` | HTTP endpoint path | `/mcp` |
| `SERVER_DEBUG` | Enable debug mode | `false` |
| `SERVER_MESSAGE_TIMEOUT` | Message timeout in seconds | `60` |

#### Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_TYPE` | Authentication type | `none` |

Available authentication types:
- `none` - No authentication (default)
- `bearer` - Bearer token authentication
- `basic` - Basic authentication
- `api_key` - API key authentication
- `cognito` - AWS Cognito authentication

##### Bearer Authentication

| Variable | Description |
|----------|-------------|
| `AUTH_TOKEN` | Bearer token |

##### Basic Authentication

| Variable | Description |
|----------|-------------|
| `AUTH_USERNAME` | Username |
| `AUTH_PASSWORD` | Password |

##### API Key Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_API_KEY` | API key value | - |
| `AUTH_API_KEY_NAME` | API key parameter name | `api_key` |
| `AUTH_API_KEY_IN` | Where to send the key | `header` |

Values for `AUTH_API_KEY_IN`: `header`, `query`, `cookie`

##### Cognito Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_COGNITO_CLIENT_ID` | Cognito client ID | - |
| `AUTH_COGNITO_USERNAME` | Username | - |
| `AUTH_COGNITO_PASSWORD` | Password | - |
| `AUTH_COGNITO_USER_POOL_ID` | User pool ID | - |
| `AUTH_COGNITO_REGION` | AWS region | `us-east-1` |

## Production Deployment

### Building for Production

```bash
# Build with specific tag
docker build -t insly/openapi-mcp-server:latest .
docker build -t insly/openapi-mcp-server:1.0.0 .

# Push to registry
docker push insly/openapi-mcp-server:latest
docker push insly/openapi-mcp-server:1.0.0
```

### Running in Production

1. **With Docker**:
```bash
docker run -d \
  --name openapi-mcp-server \
  --restart unless-stopped \
  -p 8000:8000 \
  -e API_SPEC_URL="${API_SPEC_URL}" \
  -e API_BASE_URL="${API_BASE_URL}" \
  -e AUTH_TYPE="bearer" \
  -e AUTH_TOKEN="${API_TOKEN}" \
  insly/openapi-mcp-server:latest
```

2. **With Docker Compose**:
```yaml
version: '3.8'

services:
  openapi-mcp-server:
    image: insly/openapi-mcp-server:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      API_SPEC_URL: "${API_SPEC_URL}"
      API_BASE_URL: "${API_BASE_URL}"
      AUTH_TYPE: "bearer"
      AUTH_TOKEN: "${API_TOKEN}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/mcp/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### Using Local OpenAPI Specs

To use local OpenAPI specification files:

1. Place your OpenAPI spec in a local directory (e.g., `./specs/`)
2. Update your `.env` file:

```bash
# Use local path instead of URL
API_SPEC_PATH=/app/specs/openapi.json
# Remove or comment out API_SPEC_URL
#API_SPEC_URL=
```

3. Mount the directory in `docker-compose.yml` (already included):

```yaml
volumes:
  - ./specs:/app/specs:ro
```

### Multiple APIs

To run multiple API servers:

1. Create separate `.env` files:
```bash
cp .env.example .env.api1
cp .env.example .env.api2
```

2. Create `docker-compose.multi.yml`:
```yaml
version: '3.8'

services:
  api1-mcp:
    extends:
      file: docker-compose.yml
      service: openapi-mcp-server
    container_name: api1-mcp-server
    env_file: .env.api1
    ports:
      - "8001:8000"

  api2-mcp:
    extends:
      file: docker-compose.yml
      service: openapi-mcp-server
    container_name: api2-mcp-server
    env_file: .env.api2
    ports:
      - "8002:8000"
```

3. Run both:
```bash
docker-compose -f docker-compose.multi.yml up -d
```

## Security Considerations

1. **Don't hardcode secrets** - Use environment variables or secrets management
2. **Use HTTPS** - Put the MCP server behind a reverse proxy with SSL
3. **Network isolation** - Use Docker networks to isolate services
4. **Resource limits** - Set appropriate CPU and memory limits
5. **Non-root user** - The container runs as non-root user (uid 1000)

## Monitoring

### Health Check

The server provides a health endpoint at `/mcp/health`:

```bash
curl http://localhost:8000/mcp/health
```

### Logs

View logs:
```bash
# Docker
docker logs openapi-mcp-server

# Docker Compose
docker-compose logs -f openapi-mcp-server
```

### Metrics

The server tracks basic metrics that are included in the health response:
- API calls (total, errors, error rate)
- Tool usage (total, errors, error rate)

## Troubleshooting

### Common Issues

1. **"No API spec URL or path provided"**
   - Ensure either `API_SPEC_URL` or `API_SPEC_PATH` is set

2. **"No API base URL provided"**
   - Set the `API_BASE_URL` environment variable

3. **Authentication errors**
   - Check that all required auth variables are set for your `AUTH_TYPE`
   - Verify credentials are correct

4. **Connection refused**
   - Ensure the port mapping is correct
   - Check that `SERVER_HOST` is set to `0.0.0.0` (not `localhost`)

### Debug Mode

Enable debug logging:
```bash
docker run -p 8000:8000 \
  -e SERVER_DEBUG="true" \
  -e API_SPEC_URL="..." \
  -e API_BASE_URL="..." \
  openapi-mcp-server
```