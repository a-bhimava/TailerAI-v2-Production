# TailerAI v2.0 - Production Dockerfile for Google Cloud Run
FROM python:3.11-slim

# Install system dependencies including curl and certificates
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic LaTeX engine (smaller than full TeX Live)
RUN wget -q https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@0.14.1/tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz \
    && mv tectonic /usr/local/bin/ \
    && rm tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz \
    && chmod +x /usr/local/bin/tectonic

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p data/uploads data/generated data/cache data/database logs \
    && chmod -R 755 data/ logs/

# Set environment variables for Cloud Run
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV HOST=0.0.0.0
ENV PORT=8080
ENV LATEX_ENGINE=tectonic
ENV LATEX_ENGINE_PATH=/usr/local/bin/tectonic

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check optimized for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application with optimized settings for Cloud Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]