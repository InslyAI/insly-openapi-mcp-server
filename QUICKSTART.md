# Quick Start Guide

## 🚀 Fastest Way to Start

### Using the Start Script

```bash
./start.sh
```

This script will:
1. Check if `.env` exists (creates it from `.env.example` if not)
2. Verify Docker is installed and running
3. Start the server with docker-compose
4. Wait for health check
5. Show you the server URL

## 📋 Manual Setup

### 1. Configure Environment

```bash
# Copy the template
cp .env.example .env

# Edit with your API details
nano .env
```

**Required settings in .env:**
- `API_SPEC_URL`: URL to your OpenAPI/Swagger specification
- `API_BASE_URL`: Base URL of your API

### 2. Start the Server

```bash
# Start in background
docker-compose up -d

# Or start with logs visible
docker-compose up
```

### 3. Verify It's Running

```bash
# Check health
curl http://localhost:8000/mcp/health

# View logs
docker-compose logs -f
```

## 🔧 Common Configurations

### Using Bearer Token Authentication

In `.env`:
```bash
AUTH_TYPE=bearer
AUTH_TOKEN=your-bearer-token-here
```

### Using API Key Authentication

In `.env`:
```bash
AUTH_TYPE=api_key
AUTH_API_KEY=your-api-key
AUTH_API_KEY_NAME=X-API-Key
AUTH_API_KEY_IN=header
```

### Using Local OpenAPI File

1. Place your OpenAPI spec in `./specs/` directory
2. In `.env`, use `API_SPEC_PATH` instead of `API_SPEC_URL`:
```bash
API_SPEC_PATH=/app/specs/openapi.json
# API_SPEC_URL=  # Comment out or remove
```
3. Uncomment the volumes section in `docker-compose.yml`

## 📊 Monitoring

### View Logs
```bash
docker-compose logs -f
```

### Check Status
```bash
docker-compose ps
```

### Stop Server
```bash
docker-compose down
```

## 🆘 Troubleshooting

### Port Already in Use
Change the port in `.env`:
```bash
SERVER_PORT=8080
```

### Can't Connect to API
- Check `API_BASE_URL` is correct
- Verify authentication settings
- Check server logs for errors

### Health Check Failing
- Ensure server started successfully
- Check logs: `docker-compose logs`
- Verify `.env` configuration

## 🎯 Next Steps

Once running, your AI assistant can use the server at:
```
http://localhost:8000/mcp
```

The server automatically:
- Converts your OpenAPI spec to AI-friendly tools
- Handles authentication to your API
- Provides intelligent caching
- Monitors performance

Happy coding! 🚀