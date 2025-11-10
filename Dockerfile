#
# TutorMax API - Production Dockerfile
# Multi-stage build for optimized image size
#

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies to /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 tutormax && \
    chown -R tutormax:tutormax /app

USER tutormax

# Environment variables (defaults, override in compose)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WORKERS=4 \
    HOST=0.0.0.0 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["sh", "-c", "uvicorn src.api.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}"]
