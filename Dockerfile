FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory inside container
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project configuration and skeleton for metadata validation
COPY pyproject.toml uv.lock README.md ./
COPY server/ ./server/
COPY src/ ./src/

# Install dependencies (including the local package)
RUN uv sync --frozen --no-dev

# Copy any remaining files
COPY openenv.yaml ./

# Expose port (required by HF Spaces)
EXPOSE 7860

# Ensure the app is in the path
ENV PATH="/app/.venv/bin:$PATH"

# Use the entry point defined in pyproject.toml
CMD ["server"]