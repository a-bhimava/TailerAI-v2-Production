# TailerAI v2.0 Setup Guide

This guide will help you set up TailerAI v2.0 on a new machine.

## System Requirements

- **Python**: 3.9 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: Minimum 4GB RAM
- **Storage**: At least 2GB free space
- **LaTeX**: Required for PDF generation

## Installation Steps

### 1. Install Python and Git

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python@3.11 git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git
```

**Windows:**
- Download Python 3.11+ from https://python.org
- Download Git from https://git-scm.com

### 2. Install LaTeX Distribution

**macOS:**
```bash
brew install --cask mactex
```

**Linux:**
```bash
sudo apt install texlive-full
```

**Windows:**
- Download MiKTeX from https://miktex.org

### 3. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd TailerAI-v2-Production

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration file
nano .env  # or use your preferred editor
```

**Required Configuration:**
- `GOOGLE_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `SECRET_KEY`: Generate a secure random string
- Other settings can use defaults for local development

### 5. Initialize Database

```bash
# Create data directories
mkdir -p data/database data/uploads data/generated data/cache

# Initialize database and start server
python -m app.main
```

### 6. Verify Installation

```bash
# Start the development server
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Visit `http://127.0.0.1:8002` in your browser. You should see the TailerAI interface.

## Troubleshooting

### Common Issues

**1. Python Version Error**
```bash
# Check Python version
python --version
# Should be 3.9 or higher
```

**2. LaTeX Not Found**
```bash
# Test LaTeX installation
pdflatex --version
# Should show version information
```

**3. Database Permission Error**
```bash
# Fix database directory permissions
chmod 755 data/database
```

**4. Port Already in Use**
```bash
# Find and kill process using port 8002
lsof -ti:8002 | xargs kill -9
```

**5. Missing API Key**
- Ensure `GOOGLE_API_KEY` is set in `.env` file
- Get API key from Google AI Studio
- Restart server after adding the key

### Environment Variables Reference

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here

# Optional (with defaults)
DEBUG=True
DATABASE_URL=sqlite:///./data/database/tailer.db
HOST=127.0.0.1
PORT=8002
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAX_FILE_SIZE_MB=10
REQUESTS_PER_MINUTE=60
```

### Development vs Production

**Development Setup:**
- Use SQLite database
- Enable DEBUG mode
- Use local file storage

**Production Setup:**
- Configure external database (PostgreSQL recommended)
- Disable DEBUG mode
- Set up proper file storage (AWS S3, etc.)
- Configure reverse proxy (nginx)
- Set up SSL certificates

## Next Steps

1. **Create User Account**: Register through the web interface
2. **Upload Resume Data**: Use the data import features
3. **Test Resume Generation**: Create your first tailored resume
4. **Explore Features**: Try different optimization options

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review the main README.md
3. Check the docs/ directory for additional guides
4. Ensure all dependencies are properly installed

---

**Happy Resume Tailoring!** 🚀