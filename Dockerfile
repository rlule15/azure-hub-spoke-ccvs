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
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the virtual environment from the builder stage to the runtime stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code from the builder stage to the runtime stage
COPY --from=builder /app /app

# Set the PATH environment variable to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Set the command to run the FastAPI application using uvicorn
CMD ["fastapi", "run"]