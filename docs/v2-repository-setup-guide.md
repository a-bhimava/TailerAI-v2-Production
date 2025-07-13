# TailerAI v2.0 - New Repository Setup Guide

## 🎯 Strategy: Fresh Start with Selective Migration

**Recommended Approach: Create NEW repository** for v2.0 because:
- ✅ **Clean slate** for LaTeX-focused architecture
- ✅ **Remove legacy DOCX complexity** and outdated dependencies
- ✅ **Fresh git history** without v1.0 baggage
- ✅ **Clear version separation** between DOCX (v1) and LaTeX (v2)
- ✅ **Selective migration** of only useful components

## 📋 Step-by-Step Repository Creation

### Step 1: Create New GitHub Repository

1. **Go to GitHub.com** → Sign in to your account
2. **Click "+" icon** → Select "New repository"
3. **Configure repository:**
   ```
   Repository name: tailerai-v2
   Description: AI-powered resume optimization with LaTeX formatting - Professional one-page resumes
   Visibility: Public (for free hosting and collaboration)
   Initialize: ✅ Add README file
               ✅ Add .gitignore (Python template)
               ❌ License (add later if needed)
   ```
4. **Click "Create repository"**

### Step 2: Clone New Repository Locally

```bash
# Navigate to your development directory
cd /Users/aditya/Documents/Tailer/

# Clone the new repository
git clone https://github.com/yourusername/tailerai-v2.git

# Enter the repository
cd tailerai-v2

# Verify setup
ls -la
# Should see: README.md, .gitignore
```

### Step 3: Set Up Initial Project Structure

```bash
# Create the v2.0 directory structure
mkdir -p app/{api,config,models,services,templates,utils}
mkdir -p app/api/routes
mkdir -p templates/latex
mkdir -p scripts
mkdir -p tests/{unit,integration}
mkdir -p docs
mkdir -p deploy

# Create essential files
touch app/__init__.py
touch app/main.py
touch app/config/__init__.py
touch app/config/settings.py
touch requirements.txt
touch Dockerfile
touch docker-compose.yml
touch .env.example
```

## 📁 Final Directory Structure

```
tailerai-v2/
├── README.md                    # GitHub generated
├── .gitignore                   # GitHub generated (Python)
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml          # Local development
├── cloudbuild.yaml             # Google Cloud Run deployment
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── upload.py        # File upload endpoints
│   │       ├── latex.py         # LaTeX compilation
│   │       ├── ai.py           # AI optimization
│   │       └── health.py       # Health checks
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Environment configuration
│   │   └── database.py         # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── latex_engine.py     # LaTeX compilation
│   │   ├── ai_service.py       # Gemini AI integration
│   │   ├── resume_parser.py    # Resume content extraction
│   │   └── pdf_generator.py    # PDF generation
│   ├── templates/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── file_handlers.py    # File operations
│       └── validators.py       # Input validation
├── templates/
│   └── latex/
│       ├── mspm_template.tex   # Main MSPM template
│       ├── modern_template.tex # Alternative template
│       └── components/         # Reusable LaTeX components
├── scripts/
│   ├── run-local.sh           # Local development
│   ├── deploy-cloud.sh        # Cloud deployment
│   └── setup-env.sh           # Environment setup
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Test configuration
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── docs/
│   ├── api.md                 # API documentation
│   ├── deployment.md          # Deployment guide
│   └── development.md         # Development guide
└── deploy/
    ├── cloudbuild.yaml        # Google Cloud Build
    └── terraform/             # Infrastructure as code (optional)
```

## 🔄 Selective Migration from v1.0

### What to Copy from Current Repository:

#### 1. Essential Documents
```bash
# Copy planning and documentation files
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/TailerAI_v2_plan.txt ./docs/
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/latex_v2_product_report.txt ./docs/
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/dual-deployment-strategy.md ./docs/
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/hosting-analysis-v2.md ./docs/
```

#### 2. LaTeX Template (CORE ASSET)
```bash
# Copy the MSPM LaTeX template
cp "/Users/aditya/Documents/Tailer/resume-ai-tailer/MSPM_Resume_Format_Draft_1.tex" ./templates/latex/mspm_template.tex
```

#### 3. Useful Code Components (Selective)
```bash
# Copy specific useful files (inspect first, then adapt)

# AI service integration (adapt for v2.0)
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/app/services/gemini_client.py ./app/services/

# Database models (simplify for v2.0)
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/app/models/entities.py ./app/models/
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/app/models/schemas.py ./app/models/

# Configuration patterns (adapt)
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/app/config/settings.py ./app/config/

# File handling utilities (simplify)
cp /Users/aditya/Documents/Tailer/resume-ai-tailer/app/utils/file_handlers.py ./app/utils/
```

### What NOT to Copy:

❌ **Document generation service** (DOCX-focused, replace with LaTeX)
❌ **Heavy ML dependencies** (sentence-transformers, torch)
❌ **Complex template systems** (DOCX templates)
❌ **Legacy optimization code** (outdated approaches)
❌ **Old frontend** (rebuild for LaTeX workflow)
❌ **Git history** (start fresh)

## 🛠️ Initial Setup Commands

### Step 4: Set Up Development Environment

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create basic requirements.txt
cat > requirements.txt << 'EOF'
# Core framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
alembic==1.13.1

# AI integration
google-generativeai==0.3.2

# File processing
aiofiles==23.2.1
python-docx==0.8.11

# Utilities
pydantic==2.5.0
jinja2==3.1.2

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0

# Cloud deployment
google-cloud-storage==2.10.0
google-cloud-logging==3.8.0
EOF

# Install dependencies
pip install -r requirements.txt

# Create environment template
cat > .env.example << 'EOF'
# Environment
ENVIRONMENT=local

# Database
DATABASE_URL=sqlite:///./tailerai_v2.db

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here

# LaTeX Configuration
LATEX_TIMEOUT=30
TEX_LIVE_PATH=/usr/local/texlive

# File Storage
UPLOAD_DIR=./uploads
OUTPUT_DIR=./output

# Google Cloud (for production)
GCP_PROJECT_ID=your_project_id
CLOUD_STORAGE_BUCKET=your_bucket_name

# Performance
MAX_FILE_SIZE=10485760
MAX_CONCURRENT_JOBS=5
EOF

# Copy to actual .env for local development
cp .env.example .env
```

### Step 5: Create Basic FastAPI Application

```bash
# Create main application file
cat > app/main.py << 'EOF'
"""
TailerAI v2.0 - LaTeX-powered resume optimization
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

# Create FastAPI application
app = FastAPI(
    title="TailerAI v2.0",
    description="AI-powered resume optimization with LaTeX formatting",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "TailerAI v2.0 - LaTeX Resume Generation",
        "version": "2.0.0",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
```

### Step 6: Initial Git Commit

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "🚀 Initial TailerAI v2.0 setup

- Set up project structure for LaTeX-powered resume generation
- Create FastAPI application foundation
- Add development environment configuration
- Include MSPM LaTeX template
- Prepare for dual local/cloud deployment

Features:
- Clean v2.0 architecture
- LaTeX-first approach
- Google Cloud Run ready
- Local development setup

Next: Implement LaTeX engine and AI integration"

# Push to GitHub
git push origin main
```

## 🎯 Next Development Steps

### Phase 1: Core Implementation (Week 1)
1. **Implement LaTeX engine** in `app/services/latex_engine.py`
2. **Set up database models** for resume data
3. **Create file upload endpoints** for resume processing
4. **Test basic LaTeX compilation** locally

### Phase 2: AI Integration (Week 2)
1. **Adapt Gemini AI service** for v2.0
2. **Implement content optimization** for one-page constraint
3. **Create resume parsing** from uploaded files
4. **Build template injection** system

### Phase 3: Deployment (Week 3)
1. **Set up Docker configuration** with TeX Live
2. **Configure Google Cloud Run** deployment
3. **Test production deployment**
4. **Implement monitoring and logging**

## 📋 Repository Checklist

### ✅ Completed Setup:
- [x] New GitHub repository created
- [x] Project structure established
- [x] Basic FastAPI application
- [x] Development environment configured
- [x] Essential files migrated
- [x] Initial git commit

### 🔄 Next Tasks:
- [ ] Implement LaTeX compilation service
- [ ] Set up database models
- [ ] Create API endpoints
- [ ] Test local development
- [ ] Configure cloud deployment

## 🎉 Success!

Your new TailerAI v2.0 repository is ready for development! You now have:

- ✅ **Clean foundation** for LaTeX-powered resume generation
- ✅ **Professional project structure** following best practices
- ✅ **Dual deployment setup** for local and cloud development
- ✅ **Essential components migrated** from v1.0
- ✅ **Fresh git history** without legacy baggage

**Ready to start Phase 1 development!** 🚀