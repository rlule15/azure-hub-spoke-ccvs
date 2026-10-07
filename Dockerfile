# Build stage
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


ENV UV_PYTHON_DOWNLOADS=0

# Change the working directory to /app
WORKDIR /app

# Copy the lock file and pyproject.toml to the working directory
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy the rest of the application code to the working directory
COPY . /app

# Run uv sync again to install the application dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Runtime stage

FROM python:3.13-slim AS runtime


# Install git for application use
# hadolint ignore=DL3008 # We are installing git for application use, not for building the image
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Create an unprivileged user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /sbin/nologin -M --no-log-init appuser

# Copy the application code from the builder stage to the runtime stage
COPY --from=builder --chown=1001:1001 /app /app

# Create data folder for the SQLite database
RUN mkdir -p /app/data && chown -R 1001:1001 /app/data

# Set the PATH environment variable to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Switch to the unprivileged user
USER 1001

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Container health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys,urllib.request; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3).status < 400 else sys.exit(1)"]

# Set the command to run the FastAPI application using uvicorn
CMD ["fastapi", "run"]