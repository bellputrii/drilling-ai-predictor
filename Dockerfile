# Base Python slim
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project ke container
COPY . /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Optional: create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app

# Expose port FastAPI
EXPOSE 8000

# Run as non-root user
USER appuser

# Command untuk jalankan FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]