# TailerAI v2.0: Local + Google Cloud Run Deployment Strategy

## ✅ Why This is Actually Easy

Building for both local development and Google Cloud Run is **standard practice** and offers several advantages:

- **Development Speed**: Test locally before deploying
- **Cost Efficiency**: Only pay for cloud resources when needed
- **Debugging**: Easier to debug locally
- **Flexibility**: Switch between environments seamlessly
- **CI/CD**: Automated deployments from local testing

## 🏗️ Architecture Design for Dual Deployment

### Environment-Agnostic Structure
```
tailerai-v2/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config/
│   │   ├── settings.py      # Environment-based configuration
│   │   └── database.py      # Database connection handling
│   ├── services/
│   │   ├── latex_engine.py  # LaTeX compilation service
│   │   ├── ai_service.py    # Gemini AI integration
│   │   └── pdf_generator.py # PDF generation
│   └── models/
├── templates/
│   └── mspm_template.tex    # LaTeX template
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Local development setup
├── cloudbuild.yaml         # Google Cloud Run deployment
├── .env.local              # Local environment variables
└── .env.production         # Production environment variables
```

## 🔧 Configuration Management

### 1. Environment-Based Settings
```python
# app/config/settings.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Environment detection
    environment: str = os.getenv("ENVIRONMENT", "local")
    
    # Database configuration
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./local_database.db"  # Local default
    )
    
    # LaTeX configuration
    latex_timeout: int = int(os.getenv("LATEX_TIMEOUT", "30"))
    tex_live_path: str = os.getenv("TEX_LIVE_PATH", "/usr/local/texlive")
    
    # AI service configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # File storage
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    output_dir: str = os.getenv("OUTPUT_DIR", "./output")
    
    # Cloud-specific settings
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    cloud_storage_bucket: str = os.getenv("CLOUD_STORAGE_BUCKET", "")
    
    # Performance settings
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Database Abstraction
```python
# app/config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings

# Environment-specific database setup
if settings.environment == "local":
    # Local SQLite
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
    )
elif settings.environment == "cloud_run":
    # Cloud SQL or PostgreSQL
    engine = create_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 🐳 Docker Configuration

### Universal Dockerfile
```dockerfile
# Dockerfile (works for both local and cloud)
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output temp

# Environment setup
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command (configurable via environment)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Local Development with Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=local
      - DATABASE_URL=sqlite:///./local_database.db
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
      - .:/app  # Live reload for development
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: tailerai_local
      POSTGRES_USER: local_user
      POSTGRES_PASSWORD: local_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## ☁️ Google Cloud Run Configuration

### Cloud Build Configuration
```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/tailerai-v2:$COMMIT_SHA', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/tailerai-v2:$COMMIT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'tailerai-v2'
    - '--image'
    - 'gcr.io/$PROJECT_ID/tailerai-v2:$COMMIT_SHA'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--memory'
    - '1Gi'
    - '--cpu'
    - '1'
    - '--max-instances'
    - '10'
    - '--set-env-vars'
    - 'ENVIRONMENT=cloud_run,GEMINI_API_KEY=$$GEMINI_API_KEY'
    secretEnv: ['GEMINI_API_KEY']

availableSecrets:
  secretManager:
  - versionName: projects/$PROJECT_ID/secrets/gemini-api-key/versions/latest
    env: 'GEMINI_API_KEY'
```

## 🚀 Deployment Scripts

### Local Development
```bash
#!/bin/bash
# scripts/run-local.sh

echo "🏠 Starting TailerAI v2.0 locally..."

# Load local environment
export ENVIRONMENT=local
source .env.local

# Option 1: Direct Python
echo "Starting with Python..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Docker Compose
echo "Starting with Docker Compose..."
docker-compose up --build
```

### Cloud Deployment
```bash
#!/bin/bash
# scripts/deploy-cloud.sh

echo "☁️ Deploying TailerAI v2.0 to Google Cloud Run..."

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud builds submit --config cloudbuild.yaml

echo "✅ Deployment complete!"
echo "🌐 App URL: https://tailerai-v2-YOUR_HASH-uc.a.run.app"
```

## 🎯 LaTeX Engine Adaptation

### Environment-Aware LaTeX Service
```python
# app/services/latex_engine.py
import os
import subprocess
import tempfile
from pathlib import Path
from app.config.settings import settings

class LaTeXEngine:
    def __init__(self):
        self.timeout = settings.latex_timeout
        self.temp_dir = self._get_temp_dir()
    
    def _get_temp_dir(self):
        if settings.environment == "local":
            return Path("./temp")
        else:
            # Use /tmp in Cloud Run
            return Path("/tmp")
    
    async def compile_latex(self, latex_content: str) -> bytes:
        """Compile LaTeX to PDF - works in both environments"""
        
        with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write LaTeX file
            tex_file = temp_path / "resume.tex"
            tex_file.write_text(latex_content, encoding='utf-8')
            
            # Compile command (same for both environments)
            cmd = [
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory', str(temp_path),
                str(tex_file)
            ]
            
            try:
                # Run compilation
                result = subprocess.run(
                    cmd,
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode != 0:
                    raise LaTeXCompilationError(result.stderr)
                
                # Read PDF
                pdf_file = temp_path / "resume.pdf"
                if pdf_file.exists():
                    return pdf_file.read_bytes()
                else:
                    raise LaTeXCompilationError("PDF not generated")
                    
            except subprocess.TimeoutExpired:
                raise LaTeXCompilationError("LaTeX compilation timeout")

class LaTeXCompilationError(Exception):
    pass
```

## 📊 Environment-Specific Optimizations

### Local Development Optimizations
```python
# Local-specific optimizations
if settings.environment == "local":
    # Use SQLite for simplicity
    # Enable debug logging
    # Use local file storage
    # Disable some security features for easier development
    
    import logging
    logging.basicConfig(level=logging.DEBUG)
```

### Cloud Run Optimizations
```python
# Cloud-specific optimizations
if settings.environment == "cloud_run":
    # Use Cloud SQL or external database
    # Enable production logging
    # Use Cloud Storage for files
    # Enable all security features
    # Optimize for cold starts
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Cloud Storage integration
    from google.cloud import storage
    storage_client = storage.Client()
```

## 🔄 CI/CD Pipeline

### GitHub Actions for Dual Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy TailerAI v2.0

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-local:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run local tests
        run: pytest tests/

  deploy-cloud:
    needs: test-local
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Setup Google Cloud
        uses: google-github-actions/setup-gcloud@v0
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - name: Deploy to Cloud Run
        run: gcloud builds submit --config cloudbuild.yaml
```

## 💡 Development Workflow

### Daily Development Process
1. **Code locally** with hot reload: `./scripts/run-local.sh`
2. **Test locally** with Docker: `docker-compose up`
3. **Run tests**: `pytest tests/`
4. **Commit changes**: Git commit triggers CI/CD
5. **Auto-deploy** to Cloud Run on main branch

### Environment Switching
```bash
# Switch to local development
export ENVIRONMENT=local
source .env.local

# Switch to cloud testing
export ENVIRONMENT=cloud_run
source .env.production
```

## 📈 Benefits of This Approach

### For Development:
- ✅ **Fast local iteration** with hot reload
- ✅ **Easy debugging** with local tools
- ✅ **Offline development** capability
- ✅ **Cost-free local testing**

### For Production:
- ✅ **Scalable cloud deployment**
- ✅ **Global availability** via Google Cloud
- ✅ **Auto-scaling** based on demand
- ✅ **Production-grade** infrastructure

### For Maintenance:
- ✅ **Single codebase** for both environments
- ✅ **Consistent behavior** across environments
- ✅ **Easy environment switching**
- ✅ **Automated deployments**

## 🎯 Conclusion

Building for both local and Google Cloud Run is not only **easy but recommended**! The key is:

1. **Environment-based configuration** - settings that adapt automatically
2. **Docker containerization** - ensures consistency across environments
3. **Abstracted services** - database, storage, etc. work the same way
4. **Automated CI/CD** - seamless deployment from local testing

This approach gives you the **best of both worlds**: fast local development with scalable cloud deployment.

**Ready to start building with this dual-environment approach?** 🚀