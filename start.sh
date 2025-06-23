#!/bin/bash

# OpenAPI MCP Server Quick Start Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 OpenAPI MCP Server Setup${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}📋 Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Please edit .env with your API configuration:${NC}"
        echo "   - API_SPEC_URL: Your OpenAPI specification URL"
        echo "   - API_BASE_URL: Your API base URL"
        echo "   - AUTH_TYPE: Authentication type (if needed)"
        echo ""
        echo -e "${BLUE}Run this script again after updating .env${NC}"
        exit 0
    else
        echo -e "${RED}❌ Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: docker-compose is not installed${NC}"
    echo "Please install Docker and docker-compose first"
    exit 1
fi

# Check if docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "Please start Docker first"
    exit 1
fi

# Start the server
echo -e "${BLUE}🐳 Starting OpenAPI MCP Server...${NC}"
docker-compose up -d

# Wait for health check
echo -e "${BLUE}⏳ Waiting for server to be healthy...${NC}"
sleep 5

# Check health
if curl -f http://localhost:8000/mcp/health &> /dev/null; then
    echo -e "${GREEN}✅ Server is healthy!${NC}"
    echo ""
    echo -e "${GREEN}🎉 OpenAPI MCP Server is running at:${NC}"
    echo -e "   ${BLUE}http://localhost:8000/mcp${NC}"
    echo ""
    echo -e "${YELLOW}📊 View logs:${NC} docker-compose logs -f"
    echo -e "${YELLOW}🛑 Stop server:${NC} docker-compose down"
else
    echo -e "${RED}❌ Server health check failed${NC}"
    echo -e "Check logs with: docker-compose logs"
    exit 1
fi