# ─────────────────────────────────────────────────────────────
# Stage 1 — Builder
# Installs Python dependencies and compiles required packages
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy dependency files first (better caching)
COPY /requirements.txt ./requirements.txt
COPY /pyproject.toml .

# Install dependencies into isolated directory
RUN pip install \
    --prefix=/install \
    --no-cache-dir \
    -r requirements.txt


# ─────────────────────────────────────────────────────────────
# Stage 2 — Runtime
# Lightweight runtime image
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY . /app/email_service

# Create storage and cache directories
RUN mkdir -p \
    /app/storage \
    /app/email_service/models/huggingface_cache \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    HF_HOME=/app/email_service/models/huggingface_cache \
    GMAIL_CREDENTIALS_PATH=/app/storage/credentials.json \
    GMAIL_TOKEN_PATH=/app/storage/token.json

# Expose service port
EXPOSE 8001

# Start FastAPI server
CMD ["uvicorn", "email_service.main:app", "--host", "0.0.0.0", "--port", "8001"]