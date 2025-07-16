# TailerAI v2.0 - Google Cloud Run Deployment Guide

**Version:** 2.0.0  
**Date:** July 16, 2025  
**Status:** ✅ **PRODUCTION READY**

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Project Setup](#project-setup)
4. [Container Configuration](#container-configuration)
5. [Environment Variables](#environment-variables)
6. [Database Configuration](#database-configuration)
7. [Cloud Run Deployment](#cloud-run-deployment)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Monitoring & Logging](#monitoring--logging)
10. [Security Configuration](#security-configuration)
11. [Performance Optimization](#performance-optimization)
12. [Troubleshooting](#troubleshooting)
13. [Cost Optimization](#cost-optimization)
14. [Long-term Maintenance](#long-term-maintenance)

---

## 🌟 Overview

TailerAI v2.0 is a FastAPI-based application with LaTeX PDF generation capabilities, AI content selection, and comprehensive resume tailoring features. This guide provides detailed instructions for deploying to Google Cloud Run with optimal configuration for production use.

### **Architecture Benefits for Cloud Run:**
- **Containerized**: Fully containerized with Docker
- **Stateless**: Designed for horizontal scaling
- **Health Checks**: Built-in health monitoring
- **Environment-based**: Configuration via environment variables
- **AI-Ready**: Optimized for AI service integrations

---

## 🛠️ Prerequisites

### **1. Google Cloud Account Setup**
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### **2. Development Environment**
```bash
# Required tools
- Docker Desktop
- Google Cloud SDK
- Python 3.11+
- Git

# Verify installations
docker --version
gcloud --version
python --version
```

### **3. Project Configuration**
```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # Choose your preferred region
export SERVICE_NAME="tailerai-v2"

gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
```

---

## 🚀 Project Setup

### **1. Clone and Prepare Project**
```bash
# Clone your repository
git clone https://github.com/yourusername/TailerAI-v2-Production.git
cd TailerAI-v2-Production

# Verify project structure
ls -la
# Should see: app/, data/, docs/, static/, templates/, Dockerfile, etc.
```

### **2. Local Testing**
```bash
# Build container locally
docker build -t tailerai-v2:latest .

# Test container locally
docker run -p 8080:8080 \
  -e ENVIRONMENT=production \
  -e DEBUG=False \
  -e GEMINI_API_KEY=your_key_here \
  tailerai-v2:latest

# Test health endpoint
curl http://localhost:8080/health
```

---

## 🐳 Container Configuration

### **1. Optimize Dockerfile for Cloud Run**

Create an optimized Dockerfile:

```dockerfile
# TailerAI v2.0 - Production Dockerfile for Google Cloud Run
FROM python:3.11-slim

# Install system dependencies including Tectonic LaTeX
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic LaTeX engine (smaller than full TeX Live)
RUN wget https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@0.14.1/tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz \
    && mv tectonic /usr/local/bin/ \
    && rm tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### **2. .dockerignore File**
```gitignore
# .dockerignore
.env
.env.*
.git
.gitignore
*.md
docs/
tests/
.pytest_cache/
__pycache__/
*.pyc
*.pyo
*.pyd
.coverage
htmlcov/
.vscode/
.idea/
*.log
data/cache/*
data/uploads/*
data/generated/*.pdf
```

---

## 🔐 Environment Variables

### **1. Cloud Run Environment Variables**

Create a comprehensive environment configuration:

```bash
# Create .env.production file
cat > .env.production << 'EOF'
# TailerAI v2.0 - Production Environment for Cloud Run

# Application Settings
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8080

# Database Configuration (Cloud SQL or persistent storage)
DATABASE_URL=sqlite:///./data/database/tailer_v2.db

# AI Service Configuration
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_REQUESTS_PER_MINUTE=60
GEMINI_DAILY_LIMIT=1500

# LaTeX Configuration
LATEX_ENGINE=tectonic
LATEX_ENGINE_PATH=/usr/local/bin/tectonic

# Security Settings
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# Performance Settings
MAX_FILE_SIZE=10485760
REQUEST_TIMEOUT=300

# CORS Settings
ALLOWED_ORIGINS=https://your-domain.com,https://tailerai-v2-xyz.run.app

# AI Feature Flags
ENABLE_AI_CONTENT_SELECTION=true
ENABLE_AI_ATS_OPTIMIZATION=true
ENABLE_AI_CONTENT_ENHANCEMENT=true
ENABLE_AI_PERSONALIZATION=true

# Monitoring Settings
TRACK_LEARNING_EVENTS=true
LEARNING_EVENT_RETENTION_DAYS=365

# Frontend Configuration
FRONTEND_URL=https://your-domain.com
EOF
```

### **2. Google Secret Manager Setup**

```bash
# Create secrets in Google Secret Manager
gcloud secrets create tailerai-gemini-api-key --data-file=<(echo -n "your_gemini_api_key")
gcloud secrets create tailerai-secret-key --data-file=<(echo -n "your_secret_key")
gcloud secrets create tailerai-jwt-secret --data-file=<(echo -n "your_jwt_secret")

# Verify secrets
gcloud secrets list
```

---

## 🗄️ Database Configuration

### **Option 1: Cloud SQL (Recommended for Production)**

```bash
# Create Cloud SQL instance
gcloud sql instances create tailerai-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=your_secure_password

# Create database
gcloud sql databases create tailerai_production --instance=tailerai-db

# Create database user
gcloud sql users create tailerai_user \
    --instance=tailerai-db \
    --password=your_user_password

# Update environment variable
export DATABASE_URL="postgresql://tailerai_user:password@/tailerai_production?host=/cloudsql/PROJECT_ID:REGION:tailerai-db"
```

### **Option 2: Persistent Disk (SQLite)**

```bash
# Create persistent disk for SQLite
gcloud compute disks create tailerai-data-disk \
    --size=10GB \
    --zone=us-central1-a \
    --type=pd-standard

# Mount in Cloud Run (configured in service yaml)
```

---

## 🚀 Cloud Run Deployment

### **1. Build and Push Container**

```bash
# Build and tag image
docker build -t gcr.io/$PROJECT_ID/tailerai-v2:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/tailerai-v2:latest

# Alternative: Use Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/tailerai-v2:latest .
```

### **2. Deploy to Cloud Run**

```bash
# Deploy with comprehensive configuration
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/tailerai-v2:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300s \
    --concurrency 100 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8080 \
    --set-env-vars="ENVIRONMENT=production,DEBUG=False,LOG_LEVEL=INFO,LATEX_ENGINE=tectonic" \
    --set-secrets="GEMINI_API_KEY=tailerai-gemini-api-key:latest,SECRET_KEY=tailerai-secret-key:latest,JWT_SECRET_KEY=tailerai-jwt-secret:latest"

# Get service URL
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
```

### **3. Advanced Cloud Run Configuration**

Create a `cloud-run-service.yaml` file:

```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: tailerai-v2
  namespace: 'your-project-id'
  labels:
    cloud.googleapis.com/location: us-central1
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/ingress-status: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: '10'
        autoscaling.knative.dev/minScale: '0'
        run.googleapis.com/cloudsql-instances: 'your-project-id:us-central1:tailerai-db'
        run.googleapis.com/cpu-throttling: 'true'
        run.googleapis.com/memory: 2Gi
        run.googleapis.com/cpu: '2'
        run.googleapis.com/timeout: '300s'
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/your-project-id/tailerai-v2:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: production
        - name: DEBUG
          value: 'False'
        - name: PORT
          value: '8080'
        - name: LATEX_ENGINE
          value: tectonic
        - name: LATEX_ENGINE_PATH
          value: /usr/local/bin/tectonic
        - name: DATABASE_URL
          value: 'postgresql://tailerai_user:password@/tailerai_production?host=/cloudsql/your-project-id:us-central1:tailerai-db'
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: tailerai-gemini-api-key
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: tailerai-secret-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: tailerai-jwt-secret
        resources:
          limits:
            cpu: '2'
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      serviceAccountName: 'your-service-account@your-project-id.iam.gserviceaccount.com'
  traffic:
  - percent: 100
    latestRevision: true
```

Deploy using the YAML:
```bash
gcloud run services replace cloud-run-service.yaml --region $REGION
```

---

## 🔄 CI/CD Pipeline

### **1. GitHub Actions Workflow**

Create `.github/workflows/deploy-cloud-run.yml`:

```yaml
name: Deploy to Google Cloud Run

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  PROJECT_ID: your-project-id
  REGION: us-central1
  SERVICE_NAME: tailerai-v2

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
        
    - name: Run linting
      run: |
        flake8 app/
        black --check app/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Google Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ env.PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
    
    - name: Configure Docker for GCR
      run: gcloud auth configure-docker
    
    - name: Build and Push Docker image
      run: |
        docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA .
        docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy $SERVICE_NAME \
          --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA \
          --platform managed \
          --region $REGION \
          --allow-unauthenticated \
          --memory 2Gi \
          --cpu 2 \
          --timeout 300s \
          --concurrency 100 \
          --min-instances 0 \
          --max-instances 10 \
          --set-env-vars="ENVIRONMENT=production,DEBUG=False" \
          --set-secrets="GEMINI_API_KEY=tailerai-gemini-api-key:latest,SECRET_KEY=tailerai-secret-key:latest"
    
    - name: Test deployment
      run: |
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
        curl -f $SERVICE_URL/health || exit 1
```

### **2. Cloud Build Configuration**

Create `cloudbuild.yaml`:

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/tailerai-v2:$BUILD_ID', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/tailerai-v2:$BUILD_ID']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'tailerai-v2'
      - '--image'
      - 'gcr.io/$PROJECT_ID/tailerai-v2:$BUILD_ID'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '2Gi'
      - '--cpu'
      - '2'

images:
  - 'gcr.io/$PROJECT_ID/tailerai-v2:$BUILD_ID'
```

---

## 📊 Monitoring & Logging

### **1. Google Cloud Monitoring Setup**

```bash
# Enable monitoring APIs
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Create notification channel
gcloud alpha monitoring channels create \
    --display-name="TailerAI Alerts" \
    --type=email \
    --channel-labels=email_address=admin@yourcompany.com
```

### **2. Custom Metrics and Alerts**

Create monitoring dashboard:

```yaml
# monitoring-dashboard.yaml
displayName: TailerAI v2.0 Dashboard
mosaicLayout:
  tiles:
  - width: 6
    height: 4
    widget:
      title: Request Count
      xyChart:
        dataSets:
        - timeSeriesQuery:
            timeSeriesFilter:
              filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="tailerai-v2"'
              metricType: run.googleapis.com/request_count
  - width: 6
    height: 4
    widget:
      title: Response Latency
      xyChart:
        dataSets:
        - timeSeriesQuery:
            timeSeriesFilter:
              filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="tailerai-v2"'
              metricType: run.googleapis.com/request_latencies
```

### **3. Structured Logging**

Update logging configuration in `app/main.py`:

```python
import logging
import json
from google.cloud import logging as cloud_logging

# Configure structured logging for Cloud Run
if os.getenv('ENVIRONMENT') == 'production':
    client = cloud_logging.Client()
    client.setup_logging()

class StructuredMessage:
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        return json.dumps({
            'message': self.message,
            'severity': 'INFO',
            'timestamp': datetime.utcnow().isoformat(),
            **self.kwargs
        })

# Usage
logger.info(StructuredMessage("Resume generated", user_id="123", processing_time=1.2))
```

---

## 🔒 Security Configuration

### **1. IAM and Service Accounts**

```bash
# Create service account
gcloud iam service-accounts create tailerai-v2-sa \
    --description="TailerAI v2.0 Service Account" \
    --display-name="TailerAI v2.0"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:tailerai-v2-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:tailerai-v2-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Update Cloud Run service to use service account
gcloud run services update tailerai-v2 \
    --service-account=tailerai-v2-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --region=$REGION
```

### **2. Network Security**

```bash
# Create VPC connector for private networking
gcloud compute networks vpc-access connectors create tailerai-connector \
    --region=$REGION \
    --subnet=default \
    --subnet-project=$PROJECT_ID \
    --min-instances=2 \
    --max-instances=10

# Update Cloud Run to use VPC connector
gcloud run services update tailerai-v2 \
    --vpc-connector=tailerai-connector \
    --vpc-egress=private-ranges-only \
    --region=$REGION
```

### **3. Security Headers**

Add security middleware to `app/main.py`:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add security middleware
if settings.environment == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["tailerai-v2-xyz.run.app", "your-domain.com"]
    )

# Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## ⚡ Performance Optimization

### **1. Container Optimization**

```bash
# Multi-stage build for smaller images
cat > Dockerfile.optimized << 'EOF'
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic
RUN wget -O /tmp/tectonic.tar.gz https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@0.14.1/tectonic-0.14.1-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf /tmp/tectonic.tar.gz -C /tmp \
    && mv /tmp/tectonic /usr/local/bin/ \
    && rm /tmp/tectonic.tar.gz

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
COPY . .

# Set up directories
RUN mkdir -p data/uploads data/generated data/cache data/database logs

# Non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
EOF
```

### **2. Caching Strategy**

```python
# Add Redis for caching (optional)
# In requirements.txt
redis==4.5.4

# In app/services/cache_service.py
import redis
from typing import Optional, Any
import json

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379')
        )
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
        except:
            pass
```

### **3. Database Optimization**

```python
# Connection pooling in database_service.py
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

engine = create_engine(
    database_url,
    poolclass=StaticPool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## 🐛 Troubleshooting

### **Common Issues and Solutions**

#### **1. Container Startup Issues**
```bash
# Check logs
gcloud run services logs tail tailerai-v2 --region=$REGION

# Debug container locally
docker run -it --entrypoint=/bin/bash gcr.io/$PROJECT_ID/tailerai-v2:latest
```

#### **2. Memory Issues**
```bash
# Increase memory allocation
gcloud run services update tailerai-v2 \
    --memory=4Gi \
    --region=$REGION
```

#### **3. Timeout Issues**
```bash
# Increase timeout
gcloud run services update tailerai-v2 \
    --timeout=900s \
    --region=$REGION
```

#### **4. Database Connection Issues**
```bash
# Check Cloud SQL connectivity
gcloud sql instances describe tailerai-db
gcloud sql databases list --instance=tailerai-db
```

### **Debugging Commands**

```bash
# View service details
gcloud run services describe tailerai-v2 --region=$REGION

# Check recent revisions
gcloud run revisions list --service=tailerai-v2 --region=$REGION

# View metrics
gcloud run services metrics list --service=tailerai-v2 --region=$REGION

# Test health endpoint
SERVICE_URL=$(gcloud run services describe tailerai-v2 --region=$REGION --format="value(status.url)")
curl -v $SERVICE_URL/health
```

---

## 💰 Cost Optimization

### **1. Resource Right-Sizing**

```bash
# Start with minimal resources
gcloud run services update tailerai-v2 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=5 \
    --region=$REGION

# Monitor and adjust based on metrics
```

### **2. Cost Monitoring**

```bash
# Set up budget alerts
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="TailerAI Budget" \
    --budget-amount=100USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90
```

### **3. Efficient Scaling**

```yaml
# Optimized autoscaling configuration
metadata:
  annotations:
    autoscaling.knative.dev/minScale: '0'
    autoscaling.knative.dev/maxScale: '10'
    autoscaling.knative.dev/target: '70'
    autoscaling.knative.dev/targetUtilizationPercentage: '70'
```

---

## 🔄 Long-term Maintenance

### **1. Regular Updates**

```bash
# Update dependencies
pip-review --auto

# Update base image
docker pull python:3.11-slim

# Update service
gcloud run services update tailerai-v2 \
    --image gcr.io/$PROJECT_ID/tailerai-v2:latest \
    --region=$REGION
```

### **2. Backup Strategy**

```bash
# Automated database backups
gcloud sql backups create \
    --instance=tailerai-db \
    --description="Automated backup $(date +%Y%m%d)"

# Set up automated backups
gcloud sql instances patch tailerai-db \
    --backup-start-time=03:00 \
    --backup-location=us-central1 \
    --retained-backups-count=30
```

### **3. Monitoring and Alerting**

```bash
# Create alerting policy
gcloud alpha monitoring policies create \
    --policy-from-file=alerting-policy.yaml

# Example alerting-policy.yaml
cat > alerting-policy.yaml << 'EOF'
displayName: TailerAI High Error Rate
conditions:
  - displayName: High Error Rate
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="tailerai-v2"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.1
      duration: 300s
notificationChannels:
  - projects/your-project-id/notificationChannels/NOTIFICATION_CHANNEL_ID
EOF
```

---

## 🎯 Production Checklist

### **Pre-Deployment**
- [ ] All environment variables configured
- [ ] Secrets stored in Secret Manager
- [ ] Database connection tested
- [ ] Container builds successfully
- [ ] Health checks working
- [ ] Tests passing

### **Post-Deployment**
- [ ] Health endpoint responding
- [ ] Monitoring dashboards created
- [ ] Alerting policies configured
- [ ] Backup strategy implemented
- [ ] Cost monitoring enabled
- [ ] Documentation updated

### **Security**
- [ ] IAM permissions minimal
- [ ] VPC connector configured
- [ ] SSL/TLS enabled
- [ ] Security headers added
- [ ] Audit logging enabled

---

## 📞 Support and Resources

### **Documentation**
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TailerAI v2.0 API Docs](https://your-service-url/docs)

### **Monitoring**
- [Google Cloud Console](https://console.cloud.google.com/)
- [Cloud Run Metrics](https://console.cloud.google.com/run)
- [Cloud Logging](https://console.cloud.google.com/logs)

### **Support**
- Internal documentation in `docs/` directory
- Health check endpoint: `/health`
- API documentation: `/docs`

---

## 🎉 Conclusion

This comprehensive guide provides everything needed to deploy and maintain TailerAI v2.0 on Google Cloud Run. The configuration is optimized for:

- **Production reliability**
- **Security best practices**
- **Cost optimization**
- **Scalability**
- **Long-term maintenance**

Follow this guide step by step, and you'll have a robust, production-ready deployment of TailerAI v2.0 on Google Cloud Run.

**Status:** ✅ **DEPLOYMENT READY**