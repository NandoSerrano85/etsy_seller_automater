FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (subset for migrations only)
COPY migration-requirements.txt .
RUN pip install --no-cache-dir -r migration-requirements.txt

# Copy the server code (for access to migrations and entities)
COPY server/ ./server/

# Copy migration runner
COPY migration-service/run-migrations.py .

# Set environment variables
ENV PYTHONPATH=/app

# Run migrations
CMD ["python", "run-migrations.py"]