# backend/Dockerfile
# ---------------------------------------------------------------------------
# Stage 1 – build dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for some Python packages (psycopg2, numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install into a separate directory so we can copy only the site-packages
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2 – runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="BetBot AI <ops@betbot.ai>"
LABEL description="BetBot AI FastAPI backend"

# Non-root user for security
RUN addgroup --system betbot && adduser --system --ingroup betbot betbot

WORKDIR /app

# Runtime OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=betbot:betbot . /app

# Directory for persisted ML model files
RUN mkdir -p /app/ml_models && chown betbot:betbot /app/ml_models

ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MODEL_DIR="/app/ml_models"

# Switch to non-root user
USER betbot

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ---------------------------------------------------------------------------
# Default command – run Uvicorn
# Concurrency, workers, and port can be overridden via environment variables
# or docker-compose command:
#   --workers ${WEB_CONCURRENCY:-2}
# ---------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
