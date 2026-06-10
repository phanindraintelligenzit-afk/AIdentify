# Multi-stage build for AgentsFactory
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -e ".[dev]"

# Copy examples and docs
COPY examples/ ./examples/
COPY docs/ ./docs/
COPY README.md ./

# Expose ports (FastAPI + Streamlit)
EXPOSE 8000 8501

# Default: run the API
CMD ["uvicorn", "agentkit.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
