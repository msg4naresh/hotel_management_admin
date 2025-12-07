# Use the latest Python runtime (3.14.1)
# Features: Free-threaded mode, JIT compiler, t-strings, improved performance
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for python-magic
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

# Install UV for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and README (required by hatchling build system)
COPY pyproject.toml README.md ./

# Install production dependencies only (no dev dependencies)
RUN uv sync --no-dev

# Copy the rest of the application's code
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the application using uvicorn
# Note: Health checks handled by Cloud Run, no HEALTHCHECK needed
# Run pre-start script to verify DB connectivity, then start the app
CMD uv run python backend_pre_start.py && exec uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}