# TailerAI v2.0 - Project Structure

**Last Updated:** June 30, 2025  
**Organization Status:** Fully Organized  

## Directory Structure

```
tailer_v2/
├── app/                          # Core application code
│   ├── api/                      # API layer
│   │   └── routes/               # API endpoint definitions (12 modules)
│   ├── config/                   # Application configuration
│   ├── core/                     # Core dependencies (auth, etc.)
│   ├── models/                   # Database models and schemas
│   ├── services/                 # Business logic services (13 services)
│   └── utils/                    # Utility functions
│
├── data/                         # Data storage and management
│   ├── cache/                    # Application cache
│   ├── database/                 # SQLite database files
│   ├── generated/                # System-generated files
│   ├── generated_resumes/        # Generated LaTeX/PDF resumes
│   ├── sample_data/              # Sample job descriptions and test data
│   ├── tests/                    # Test-specific data files
│   └── uploads/                  # User-uploaded files
│
├── deploy/                       # Deployment configurations
│
├── docs/                         # Documentation
│   ├── DEVELOPMENT_STATUS.md     # Current development status
│   ├── PROJECT_BLUEPRINT.md      # Technical blueprint and best practices
│   ├── PROJECT_STRUCTURE.md     # This file - project organization
│   ├── Tailer_v2_PRDs.md         # Product Requirements Documents
│   └── [other documentation]     # Additional technical docs
│
├── reports/                      # Test reports and analysis
│   ├── pipeline_test_summary.md  # End-to-end pipeline test results
│   ├── tailer_v2_project_status_report_*.md  # Status reports
│   ├── *_test_results.json       # Test execution results
│   └── quality_*.md              # Quality assurance reports
│
├── scripts/                      # Utility and debug scripts
│   ├── debug_*.py                # Debug and development scripts
│   └── [utility scripts]         # Other maintenance scripts
│
├── static/                       # Frontend assets
│   ├── assets/                   # Static assets
│   ├── css/                      # Stylesheets (5 CSS files)
│   ├── js/                       # JavaScript files (7 JS modules)
│   └── index.html                # Main frontend interface
│
├── templates/                    # Document templates
│   └── latex/                    # LaTeX resume templates
│       ├── mspm_template.tex     # Main MSPM template
│       └── sample_*.tex          # Sample templates
│
├── tests/                        # Test suites
│   ├── api/                      # API endpoint tests
│   ├── integration/              # Integration tests
│   ├── manual/                   # Manual test scripts (moved from root)
│   │   ├── test_*.py             # Individual service tests
│   │   └── test_*.json           # Test data files
│   ├── services/                 # Service-specific tests
│   └── unit/                     # Unit tests
│
└── [Root Files]                  # Configuration and setup
    ├── .env / .env.example       # Environment configuration
    ├── .gitignore                # Git ignore rules
    ├── Dockerfile                # Container configuration
    ├── README.md                 # Project overview
    └── requirements.txt          # Python dependencies
```

## File Organization Summary

### ✅ **Organized Files (Moved from Root)**

#### **Test Files → `tests/manual/`**
- `test_*.py` (12 test files) - Individual component tests
- `test_*.json` (1 file) - Test configuration data

#### **Reports → `reports/`**
- `pipeline_test_summary.md` - End-to-end pipeline test results
- `*_test_results.json` (2 files) - Authentication and dataset test results
- Status reports and quality assessments

#### **Generated Content → `data/generated_resumes/`**
- `aditya_pm_optimized_resume.tex` - LaTeX source
- `aditya_pm_optimized_resume.pdf` - Generated PDF (44.5 KB)
- `aditya_pm_optimized_resume.aux/.log` - LaTeX compilation artifacts

#### **Sample Data → `data/sample_data/`**
- `sample_job_description.txt` - Product Manager job posting

#### **Scripts → `scripts/`**
- `debug_*.py` (2 files) - Debug and development utilities

### **Core Application Structure**

#### **Backend Services (13 Services)**
Located in `app/services/`:
- `auth_service.py` - Authentication and user management
- `master_dataset_service.py` - Resume data management
- `job_analysis_service.py` - AI-powered job analysis
- `content_selection_service.py` - Intelligent content selection
- `latex_generation_service.py` - PDF generation
- `ats_optimization_service.py` - ATS compatibility
- `quality_control_service.py` - Quality assessment
- [Additional services for other features]

#### **API Routes (12 Modules)**
Located in `app/api/routes/`:
- `auth.py` - Authentication endpoints
- `master_dataset.py` - Dataset management
- `latex_generation.py` - PDF generation
- `quality_control.py` - Quality assessment
- [Additional route modules]

#### **Database Models**
Located in `app/models/`:
- `database.py` - SQLAlchemy models (15+ tables)
- `entities.py` - Business entities
- `schemas.py` - Pydantic validation schemas

### **Frontend Structure**

#### **Static Assets** (`static/`)
- **CSS Files (5):** components.css, layout.css, reset.css, responsive.css, variables.css
- **JavaScript (7):** api.js, app.js, auth.js, dataset.js, navigation.js, notifications.js, utils.js
- **Main Interface:** index.html (371 lines)

### **Data Management**

#### **Database** (`data/database/`)
- `tailer_v2.db` - Main SQLite database

#### **File Storage** (`data/`)
- `uploads/` - User-uploaded resumes
- `generated_resumes/` - Generated LaTeX/PDF files
- `cache/` - Application cache
- `sample_data/` - Sample data for testing

### **Testing Structure**

#### **Test Categories**
- **Manual Tests** (`tests/manual/`) - Individual component validation
- **Integration Tests** (`tests/integration/`) - End-to-end workflows  
- **Unit Tests** (`tests/unit/`) - Isolated function testing
- **API Tests** (`tests/api/`) - Endpoint validation

### **Documentation** (`docs/`)
- **Technical Specs:** PRDs, blueprints, development status
- **Project Organization:** This structure document
- **User Guides:** Workflow documentation

## Clean Root Directory

The root directory now contains only essential configuration files:
- `.env` / `.env.example` - Environment configuration
- `.gitignore` - Git ignore rules
- `Dockerfile` - Container setup
- `README.md` - Project overview
- `requirements.txt` - Python dependencies

## Organization Benefits

### **✅ Improved Maintainability**
- Clear separation of concerns
- Easy navigation and file discovery
- Consistent organization patterns

### **✅ Enhanced Development Workflow**
- Test files organized by type and scope
- Reports easily accessible for analysis
- Debug scripts separated from core code

### **✅ Professional Structure**
- Industry-standard directory layout
- Clean root directory
- Logical file grouping

### **✅ Scalability Ready**
- Room for growth in each category
- Clear conventions for new files
- Modular organization supports team development

## File Naming Conventions

### **Tests**
- `test_[component_name].py` - Component-specific tests
- `test_[component_name]_simple.py` - Simplified test versions

### **Reports**
- `[subject]_test_results.json` - Test execution results
- `[subject]_report_[timestamp].md` - Analysis reports

### **Generated Content**
- `[name]_[role]_optimized_resume.[ext]` - Generated resumes
- `sample_[type].txt` - Sample data files

## Maintenance Notes

- **Regular Cleanup:** Remove old temporary files and logs
- **Test Organization:** Keep test files updated and organized by feature
- **Report Archival:** Archive old reports to maintain performance
- **Documentation Updates:** Keep structure documentation current

---

**Project Status:** Fully organized and ready for development  
**Next Steps:** Continue development with clean, organized structure