"""
TailerAI v2.0 - Master Dataset Resume Generator
Main FastAPI application entry point with database initialization.
Following project blueprint best practices for startup and error handling.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
from pathlib import Path

from app.config.settings import get_settings
from app.api.routes import upload, analysis, generation, optimization, master_dataset, auth, ats_optimization, latex_generation, quality_control, export, applications, ai_content_selection, content_enhancement_api
from app.services.database_service import initialize_database, db_service, create_sample_data
from app.api.dependencies.auth_deps import limiter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Handles startup and shutdown events following blueprint practices.
    """
    # Startup
    logger.info("Starting TailerAI v2.0 with Master Dataset Architecture")
    
    try:
        # Initialize database
        initialize_database()
        logger.info("Database initialization completed")
        
        # Create sample data in development mode (disabled to prevent UUID errors)
        # if settings.DEBUG:
        #     try:
        #         create_sample_data()
        #         logger.info("Sample data created for development")
        #     except Exception as e:
        #         logger.warning(f"Sample data creation failed (may already exist): {str(e)}")
        
        # Validate critical services
        db_health = db_service.health_check()
        if db_health["status"] != "healthy":
            logger.error(f"Database health check failed: {db_health}")
            raise Exception("Database is not healthy")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.critical(f"Application startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down TailerAI v2.0")
    # Add cleanup tasks here if needed

app = FastAPI(
    title="TailerAI v2.0 - Master Dataset Engine",
    description="Intelligent content selection from comprehensive master dataset for ATS-optimized resumes",
    version="2.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/v2/auth", tags=["authentication"])
app.include_router(master_dataset.router, prefix="/api/v2/master-dataset", tags=["master-dataset"])
app.include_router(upload.router, prefix="/api/v2", tags=["upload"])
app.include_router(analysis.router, prefix="/api/v2", tags=["analysis"])
app.include_router(generation.router, prefix="/api/v2", tags=["generation"])
app.include_router(optimization.router, prefix="/api/v2", tags=["optimization"])
app.include_router(ats_optimization.router, prefix="/api/v2/ats", tags=["ats-optimization"])
app.include_router(latex_generation.router, tags=["latex-generation"])
app.include_router(quality_control.router)

# Phase 1: Enhanced AI Content Selection (Gemini Integration)
app.include_router(ai_content_selection.router, tags=["ai-content-selection"])

# Phase 3: Content Enhancement Engine (Gemini Integration)
app.include_router(content_enhancement_api.router, tags=["content-enhancement"])

# PRD-011: Export & Personal Application Management routes
app.include_router(export.router, tags=["export"])
app.include_router(applications.router, tags=["applications"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve static files
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend page"""
    frontend_file = Path(__file__).parent.parent / "static" / "index.html"
    if frontend_file.exists():
        return frontend_file.read_text()
    return """
    <html>
        <head><title>TailerAI v2.0</title></head>
        <body>
            <h1>TailerAI v2.0 - LaTeX Resume Generator</h1>
            <p>Welcome to TailerAI v2.0! Upload your resume and job description to get started.</p>
            <p>API Documentation: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """
    Enhanced health check endpoint.
    Following blueprint practices for comprehensive service monitoring.
    """
    try:
        # Check database health
        db_health = db_service.health_check()
        
        # Check critical services
        services_status = {
            "database": db_health["status"] == "healthy",
            "latex_engine": Path(settings.latex_engine_path).exists() if settings.latex_engine_path else False,
            "api": True  # If we're here, API is working
        }
        
        overall_status = "healthy" if all(services_status.values()) else "degraded"
        
        return {
            "status": overall_status,
            "version": "2.0.0",
            "environment": settings.environment,
            "architecture": "master_dataset",
            "services": services_status,
            "database": db_health,
            "debug_mode": settings.DEBUG
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "version": "2.0.0",
            "environment": settings.environment,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )