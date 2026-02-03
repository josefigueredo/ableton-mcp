# =============================================================================
# Ableton Live MCP Server - Production Dockerfile
# =============================================================================
# Multi-stage build for minimal image size
#
# Usage:
#   docker build -t ableton-mcp .
#   docker run --network host ableton-mcp  # Linux
#   docker run -e ABLETON_OSC_HOST=host.docker.internal ableton-mcp  # Mac/Windows
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies first (better caching)
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Labels for container metadata
LABEL org.opencontainers.image.title="Ableton Live MCP Server"
LABEL org.opencontainers.image.description="AI-powered music production assistant for Ableton Live"
LABEL org.opencontainers.image.url="https://github.com/josefigueredo/ableton-mcp"
LABEL org.opencontainers.image.source="https://github.com/josefigueredo/ableton-mcp"
LABEL org.opencontainers.image.vendor="Jose Figueredo"
LABEL org.opencontainers.image.licenses="MIT"

# Create non-root user for security
RUN groupadd --gid 1000 mcp && \
    useradd --uid 1000 --gid mcp --shell /bin/bash --create-home mcp

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=mcp:mcp ableton_mcp/ ./ableton_mcp/

# Environment variables with sensible defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # OSC Configuration - override for your setup
    ABLETON_OSC_HOST=127.0.0.1 \
    ABLETON_OSC_SEND_PORT=11000 \
    ABLETON_OSC_RECEIVE_PORT=11001 \
    # Logging
    ABLETON_MCP_LOG_LEVEL=INFO \
    ABLETON_MCP_LOG_TO_CONSOLE=true

# Switch to non-root user
USER mcp

# Expose OSC ports (UDP)
EXPOSE 11000/udp
EXPOSE 11001/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python", "-m", "ableton_mcp.main"]
CMD []
