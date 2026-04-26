FROM python:3.13-slim

# Install system deps (ffmpeg for video processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    awscli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create local storage dir for video files
RUN mkdir -p /app/local_storage/raw /app/local_storage/processed

EXPOSE 8000

# Default: API server (override for worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
