FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create log directory
RUN mkdir -p /var/log && chmod 777 /var/log

# Set Python path
ENV PYTHONPATH=/app/src

# Run the service
CMD ["python", "src/main.py"]
