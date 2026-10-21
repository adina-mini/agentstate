FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy source code and scripts
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example ./.env

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "agentgate.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
