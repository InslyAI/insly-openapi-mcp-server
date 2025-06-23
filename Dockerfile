# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install --user --no-cache-dir -e .

# Final stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcp

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/mcp/.local

# Copy application code
COPY --chown=mcp:mcp . .

# Switch to non-root user
USER mcp

# Add user's local bin to PATH
ENV PATH=/home/mcp/.local/bin:$PATH

# Default environment variables
ENV PYTHONUNBUFFERED=1 \
    API_NAME="OpenAPI MCP Server" \
    AUTH_TYPE="none" \
    SERVER_HOST="0.0.0.0" \
    SERVER_PORT="8000" \
    SERVER_PATH="/mcp" \
    SERVER_DEBUG="false" \
    SERVER_MESSAGE_TIMEOUT="300"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}${SERVER_PATH}/health || exit 1

# Run the server
CMD ["python", "-m", "insly.openapi_mcp_server.server"]