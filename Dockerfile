# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY insly ./insly

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install .

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 mcp

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder --chown=mcp:mcp /opt/venv /opt/venv

# Copy application code
COPY --chown=mcp:mcp insly ./insly

# Set up environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER mcp

EXPOSE 8000 8001

# Simple health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import insly.openapi_mcp_server; print('OK')" || exit 1

# Run the application
CMD ["python", "-m", "insly.openapi_mcp_server.server"]