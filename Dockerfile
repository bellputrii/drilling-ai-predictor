# Base Python slim
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies OS-level
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Upgrade pip dan install dependencies Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Optional: non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app

# Set user
USER appuser

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]