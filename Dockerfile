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
RUN apt-get update && apt-get install -y --no-install-recommends \
    git=2.55.0-1ubuntu1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Create an unprivileged user and switch to that user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /sbin/nologin -M --no-log-init appuser

# Create data folder for the SQLite database
RUN mkdir -p /app/data && chown -R appuser:appgroup /app/data

# Copy the virtual environment from the builder stage to the runtime stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code from the builder stage to the runtime stage
COPY --from=builder /app /app

# Set the PATH environment variable to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Switch to the unprivileged user
USER 1001

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Set the command to run the FastAPI application using uvicorn
CMD ["fastapi", "run"]