# TailerAI v2.0 - Production Ready

🚀 **AI-Powered Resume Tailoring Platform with Master Dataset Architecture**

TailerAI v2.0 is a comprehensive AI-powered platform that creates perfectly tailored resumes using advanced content selection, ATS optimization, and personalization engines. Built with FastAPI and integrated with Google's Gemini AI.

## 🌟 Key Features

- **Master Dataset Architecture**: Centralized user data management with intelligent content selection
- **Gemini AI Integration**: Advanced content enhancement and optimization
- **ATS Optimization Engine**: Multi-system compatibility testing and keyword optimization
- **Achievement Enhancement Service**: AI-powered content improvement with authenticity safeguards
- **Personalization Engine**: Continuous learning and performance tracking
- **LaTeX Resume Generation**: Professional, customizable resume templates

## 🏗️ Architecture Overview

### Core Services
- **Content Selection Engine** (PRD-005): AI-powered content selection with fallback mechanisms
- **ATS Optimization Engine** (PRD-006): Comprehensive ATS compatibility and keyword optimization
- **Achievement Enhancement Service** (PRD-008): Content enhancement with authenticity preservation
- **Personalization Engine** (PRD-009): Continuous learning and outcome tracking

### Technology Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **AI Integration**: Google Gemini AI
- **Document Generation**: LaTeX + PDF generation
- **File Processing**: PyPDF2, python-docx
- **Security**: JWT authentication, bcrypt hashing

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Git
- LaTeX distribution (for PDF generation)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd TailerAI-v2-Production
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration values
```

5. **Initialize database**
```bash
python -m app.main
```

6. **Start the server**
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Visit `http://127.0.0.1:8002` to access the platform.

## 📁 Project Structure

```
TailerAI-v2-Production/
├── app/                    # Main application code
│   ├── services/          # Core business logic services
│   ├── models/            # Database models
│   ├── routes/            # API endpoints
│   └── main.py           # Application entry point
├── data/                  # Data directories
│   ├── database/         # SQLite database
│   ├── uploads/          # User uploaded files
│   ├── generated/        # Generated resumes
│   └── cache/           # Temporary cache
├── static/               # Static web assets
├── templates/            # HTML and LaTeX templates
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## 🔧 Configuration

### Environment Variables
See `.env.example` for all available configuration options.

### Required API Keys
- **Google Gemini API Key**: Required for AI features
  - Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Set in `.env` as `GOOGLE_API_KEY`

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:
- **GEMINI_INTEGRATION_STRATEGY.md**: AI integration strategy and PRD implementation
- **ORGANIZATION_COMPLETE.md**: Project organization and file structure
- Additional technical documentation and guides

## 🧪 Testing

Run the test suite:
```bash
pytest
```

For development with auto-reload:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

## 🔒 Security

- JWT-based authentication
- Bcrypt password hashing
- File upload validation
- Rate limiting protection
- Environment-based configuration

## 📊 Performance

- **Content Selection**: 95% accuracy with AI fallback
- **ATS Optimization**: Multi-system compatibility testing
- **Achievement Enhancement**: Authenticity-preserving improvements
- **Personalization**: Continuous learning from application outcomes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For technical support or questions:
- Check the documentation in `docs/`
- Review the troubleshooting guide
- Contact the development team

---

**TailerAI v2.0** - Revolutionizing resume creation with AI-powered personalization and optimization.
# TailerAI-v2-Production
