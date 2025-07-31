# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies to a virtual environment
RUN uv sync --frozen

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY src/ ./src/

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add venv to path
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "src.whatsapp_image_bot.app:app", "--host", "0.0.0.0", "--port", "8000"]