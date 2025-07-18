"""
TailerAI v2.0 Configuration Settings
Environment-based configuration for local and cloud deployment
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "TailerAI v2.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:8000", 
            "http://localhost:8002",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8002"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # Database settings (following blueprint best practices)
    database_url: str = Field(
        default="sqlite:///./data/database/tailer_v2.db",
        env="DATABASE_URL"
    )
    
    # Cloud SQL specific settings
    cloud_sql_instance: str = Field(default="", env="CLOUD_SQL_INSTANCE")
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")  # 1 hour
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    db_pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
    
    # AI Service settings
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_requests_per_minute: int = Field(default=60, env="GEMINI_REQUESTS_PER_MINUTE")
    gemini_daily_limit: int = Field(default=1500, env="GEMINI_DAILY_LIMIT")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    
    # Enhanced AI Content Selection settings
    enable_ai_content_selection: bool = Field(default=True, env="ENABLE_AI_CONTENT_SELECTION")
    ai_selection_fallback_enabled: bool = Field(default=True, env="AI_SELECTION_FALLBACK_ENABLED")
    ai_selection_confidence_threshold: float = Field(default=0.7, env="AI_SELECTION_CONFIDENCE_THRESHOLD")
    ai_selection_default_method: str = Field(default="ai_enhanced", env="AI_SELECTION_DEFAULT_METHOD")
    
    # Phase 2: ATS Optimization Engine settings
    enable_ai_ats_optimization: bool = Field(default=False, env="ENABLE_AI_ATS_OPTIMIZATION")
    ats_optimization_fallback_enabled: bool = Field(default=True, env="ATS_OPTIMIZATION_FALLBACK_ENABLED")
    ats_optimization_confidence_threshold: float = Field(default=0.7, env="ATS_OPTIMIZATION_CONFIDENCE_THRESHOLD")
    ats_default_target_systems: str = Field(default="taleo,workday,generic", env="ATS_DEFAULT_TARGET_SYSTEMS")
    
    # Phase 3: Content Enhancement Engine settings
    enable_ai_content_enhancement: bool = Field(default=False, env="ENABLE_AI_CONTENT_ENHANCEMENT")
    content_enhancement_fallback_enabled: bool = Field(default=True, env="CONTENT_ENHANCEMENT_FALLBACK_ENABLED")
    content_enhancement_confidence_threshold: float = Field(default=0.7, env="CONTENT_ENHANCEMENT_CONFIDENCE_THRESHOLD")
    content_enhancement_default_level: str = Field(default="moderate", env="CONTENT_ENHANCEMENT_DEFAULT_LEVEL")
    
    # Phase 4: Continuous Learning & Personalization settings
    enable_ai_personalization: bool = Field(default=False, env="ENABLE_AI_PERSONALIZATION")
    personalization_fallback_enabled: bool = Field(default=True, env="PERSONALIZATION_FALLBACK_ENABLED")
    personalization_confidence_threshold: float = Field(default=0.7, env="PERSONALIZATION_CONFIDENCE_THRESHOLD")
    personalization_min_data_points: int = Field(default=5, env="PERSONALIZATION_MIN_DATA_POINTS")
    personalization_learning_window_days: int = Field(default=365, env="PERSONALIZATION_LEARNING_WINDOW_DAYS")
    
    # A/B Testing settings
    enable_ab_testing: bool = Field(default=False, env="ENABLE_AB_TESTING")
    ab_test_default_duration_days: int = Field(default=30, env="AB_TEST_DEFAULT_DURATION_DAYS")
    ab_test_min_sample_size: int = Field(default=100, env="AB_TEST_MIN_SAMPLE_SIZE")
    ab_test_confidence_level: float = Field(default=0.95, env="AB_TEST_CONFIDENCE_LEVEL")
    
    # Market Intelligence settings
    enable_market_intelligence: bool = Field(default=False, env="ENABLE_MARKET_INTELLIGENCE")
    market_intelligence_refresh_hours: int = Field(default=24, env="MARKET_INTELLIGENCE_REFRESH_HOURS")
    market_intelligence_data_sources: List[str] = Field(default=["user_outcomes", "gemini_analysis"], env="MARKET_INTELLIGENCE_DATA_SOURCES")
    
    # Learning Event settings
    track_learning_events: bool = Field(default=True, env="TRACK_LEARNING_EVENTS")
    learning_event_retention_days: int = Field(default=365, env="LEARNING_EVENT_RETENTION_DAYS")
    auto_reanalyze_trigger_count: int = Field(default=3, env="AUTO_REANALYZE_TRIGGER_COUNT")
    
    # LaTeX settings
    latex_engine: str = Field(default="pdflatex", env="LATEX_ENGINE")
    latex_engine_path: str = Field(default="/usr/bin/pdflatex", env="LATEX_ENGINE_PATH")
    tex_live_path: str = Field(default="/usr/local/texlive", env="TEX_LIVE_PATH")
    
    # File storage settings
    data_dir: str = Field(default="./data", env="DATA_DIR")
    upload_dir: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    output_dir: str = Field(default="./data/generated", env="OUTPUT_DIR")
    cache_dir: str = Field(default="./data/cache", env="CACHE_DIR")
    
    # Template settings
    latex_template_dir: str = Field(default="./templates/latex", env="LATEX_TEMPLATE_DIR")
    default_template: str = Field(default="mspm_template.tex", env="DEFAULT_TEMPLATE")
    
    # Performance settings
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    
    # Security settings
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="dev-jwt-secret-change-in-production", env="JWT_SECRET_KEY")
    
    # Frontend settings
    frontend_url: str = Field(default="http://localhost:8000", env="FRONTEND_URL")
    
    # SMTP settings for email
    smtp_host: str = Field(default="", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@tailerai.com", env="SMTP_FROM_EMAIL")
    
    # Google OAuth settings
    google_client_id: str = Field(default="1008899385069-rjplcqd5q2ml6504f5epmd720uth9tme.apps.googleusercontent.com", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="http://localhost:8002", env="GOOGLE_REDIRECT_URI")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()
        self._validate_latex_setup()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.data_dir,
            f"{self.data_dir}/database",
            self.upload_dir,
            self.output_dir,
            self.cache_dir,
            self.latex_template_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _validate_latex_setup(self):
        """Validate Tectonic LaTeX engine installation"""
        if self.environment == "production":
            import subprocess
            try:
                # Test if tectonic is available in PATH
                result = subprocess.run(['tectonic', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    print(f"Warning: Tectonic LaTeX engine not available")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print(f"Warning: Tectonic LaTeX engine not found in PATH")
    
    @property
    def DEBUG(self) -> bool:
        """Uppercase property for compatibility with database service"""
        return self.debug
    
    @property
    def DATA_DIR(self) -> str:
        """Uppercase property for compatibility with database service"""
        return self.data_dir
    
    @property
    def DATABASE_URL(self) -> str:
        """Uppercase property for compatibility with database service"""
        return self.database_url
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def database_path(self) -> str:
        """Get the database file path for SQLite"""
        if self.database_url.startswith("sqlite"):
            return self.database_url.replace("sqlite:///", "")
        return self.database_url

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings