"""
Database service for TailerAI v2.0 Master Dataset.
Handles database connections, migrations, and initialization.
Following project blueprint best practices for error handling and modularity.
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.config.settings import get_settings
from app.models.database import Base, QualityAssessment

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class DatabaseService:
    """
    Database service following blueprint best practices.
    Handles connections, sessions, and error management.
    """
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Initialize database connection and session factory.
        Uses environment-based configuration as per blueprint.
        """
        try:
            # Create engine based on environment
            if settings.DEBUG:
                # SQLite for development (as per blueprint)
                database_url = f"sqlite:///{settings.DATA_DIR}/database/tailer_v2.db"
                self.engine = create_engine(
                    database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=settings.DEBUG  # SQL logging in debug mode
                )
                
                # Ensure database directory exists
                db_path = Path(settings.DATA_DIR) / "database"
                db_path.mkdir(parents=True, exist_ok=True)
                
            else:
                # PostgreSQL for production (as per blueprint)
                database_url = settings.DATABASE_URL
                if not database_url:
                    raise DatabaseError("DATABASE_URL not configured for production")
                
                self.engine = create_engine(
                    database_url,
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,   # Recycle connections every hour
                    max_overflow=20,     # Allow extra connections under load
                    echo=False
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self._initialized = True
            logger.info(f"Database initialized successfully. Debug mode: {settings.DEBUG}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")
    
    def create_tables(self) -> None:
        """
        Create all database tables.
        Following blueprint practices for safe schema management.
        """
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        try:
            # Create all tables defined in Base metadata
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise DatabaseError(f"Table creation failed: {str(e)}")
    
    def drop_tables(self) -> None:
        """
        Drop all database tables. Use with caution!
        Only available in debug mode for safety.
        """
        if not settings.DEBUG:
            raise DatabaseError("Table dropping only allowed in debug mode")
        
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            raise DatabaseError(f"Table dropping failed: {str(e)}")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup.
        Following blueprint practices for error handling and resource management.
        """
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error: {str(e)}")
            raise DatabaseError(f"Data integrity violation: {str(e)}")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error in database session: {str(e)}")
            raise DatabaseError(f"Unexpected database error: {str(e)}")
            
        finally:
            session.close()
    
    def health_check(self) -> dict:
        """
        Perform database health check.
        Returns status information for monitoring.
        """
        if not self._initialized:
            return {"status": "error", "message": "Database not initialized"}
        
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                
                return {
                    "status": "healthy",
                    "database_type": "sqlite" if settings.DEBUG else "postgresql",
                    "debug_mode": settings.DEBUG
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "error", 
                "message": str(e),
                "database_type": "sqlite" if settings.DEBUG else "postgresql"
            }
    
    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> Any:
        """
        Execute raw SQL with proper error handling.
        Use sparingly and only when ORM is insufficient.
        """
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        try:
            with self.get_session() as session:
                result = session.execute(text(sql), params or {})
                return result.fetchall()
                
        except SQLAlchemyError as e:
            logger.error(f"Raw SQL execution failed: {sql[:100]}... Error: {str(e)}")
            raise DatabaseError(f"SQL execution failed: {str(e)}")
    
    def get_table_info(self) -> dict:
        """
        Get information about database tables and their sizes.
        Useful for monitoring and debugging.
        """
        if not self._initialized:
            return {"error": "Database not initialized"}
        
        try:
            table_info = {}
            
            if settings.DEBUG:
                # SQLite table information
                with self.get_session() as session:
                    tables_result = session.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ))
                    tables = [row[0] for row in tables_result.fetchall()]
                    
                    for table in tables:
                        count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.fetchone()[0]
                        table_info[table] = {"row_count": count}
            else:
                # PostgreSQL table information
                with self.get_session() as session:
                    result = session.execute(text("""
                        SELECT table_name, 
                               COALESCE(n_tup_ins, 0) as row_count
                        FROM information_schema.tables t
                        LEFT JOIN pg_stat_user_tables s ON t.table_name = s.relname
                        WHERE table_schema = 'public'
                    """))
                    
                    for row in result.fetchall():
                        table_info[row[0]] = {"row_count": row[1] or 0}
            
            return {"status": "success", "tables": table_info}
            
        except Exception as e:
            logger.error(f"Failed to get table info: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def create_quality_assessment(self, assessment_data: dict) -> QualityAssessment:
        """
        Create a new quality assessment record in the database.
        """
        try:
            with self.get_session() as session:
                assessment = QualityAssessment(**assessment_data)
                session.add(assessment)
                session.flush()
                session.refresh(assessment)
                return assessment
                
        except Exception as e:
            logger.error(f"Failed to create quality assessment: {str(e)}")
            raise DatabaseError(f"Quality assessment creation failed: {str(e)}")
    
    def get_quality_assessment(self, assessment_id: str) -> Optional[QualityAssessment]:
        """
        Retrieve a quality assessment by ID.
        """
        try:
            with self.get_session() as session:
                assessment = session.query(QualityAssessment).filter(
                    QualityAssessment.id == assessment_id
                ).first()
                return assessment
                
        except Exception as e:
            logger.error(f"Failed to get quality assessment {assessment_id}: {str(e)}")
            raise DatabaseError(f"Quality assessment retrieval failed: {str(e)}")
    
    def get_user_quality_assessments(self, profile_id: str, limit: int = 10) -> list[QualityAssessment]:
        """
        Get recent quality assessments for a user profile.
        """
        try:
            with self.get_session() as session:
                assessments = session.query(QualityAssessment).filter(
                    QualityAssessment.profile_id == profile_id
                ).order_by(QualityAssessment.assessed_at.desc()).limit(limit).all()
                return assessments
                
        except Exception as e:
            logger.error(f"Failed to get user quality assessments for {profile_id}: {str(e)}")
            raise DatabaseError(f"User quality assessments retrieval failed: {str(e)}")
    
    def update_quality_assessment(self, assessment_id: str, update_data: dict) -> Optional[QualityAssessment]:
        """
        Update an existing quality assessment.
        """
        try:
            with self.get_session() as session:
                assessment = session.query(QualityAssessment).filter(
                    QualityAssessment.id == assessment_id
                ).first()
                
                if assessment:
                    for key, value in update_data.items():
                        if hasattr(assessment, key):
                            setattr(assessment, key, value)
                    session.flush()
                    session.refresh(assessment)
                
                return assessment
                
        except Exception as e:
            logger.error(f"Failed to update quality assessment {assessment_id}: {str(e)}")
            raise DatabaseError(f"Quality assessment update failed: {str(e)}")


# Global database service instance
db_service = DatabaseService()


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    Following blueprint practices for dependency injection.
    """
    with db_service.get_session() as session:
        yield session


def initialize_database() -> None:
    """
    Initialize database with error handling.
    Called during application startup.
    """
    try:
        db_service.initialize()
        db_service.create_tables()
        logger.info("Database initialization completed successfully")
        
    except DatabaseError as e:
        logger.critical(f"Database initialization failed: {str(e)}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during database initialization: {str(e)}")
        raise DatabaseError(f"Database setup failed: {str(e)}")


def reset_database() -> None:
    """
    Reset database by dropping and recreating tables.
    Only available in debug mode for safety.
    """
    if not settings.DEBUG:
        raise DatabaseError("Database reset only allowed in debug mode")
    
    try:
        db_service.drop_tables()
        db_service.create_tables()
        logger.info("Database reset completed successfully")
        
    except DatabaseError as e:
        logger.error(f"Database reset failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database reset: {str(e)}")
        raise DatabaseError(f"Database reset failed: {str(e)}")


# Database migration utilities
def run_migration(migration_file: str) -> None:
    """
    Run a specific migration file.
    Simple migration system following blueprint practices.
    """
    if not settings.DEBUG:
        logger.warning("Manual migrations should be handled by deployment system in production")
    
    migration_path = Path(__file__).parent.parent.parent / "migrations" / migration_file
    
    if not migration_path.exists():
        raise DatabaseError(f"Migration file not found: {migration_file}")
    
    try:
        with open(migration_path, 'r') as f:
            sql_content = f.read()
        
        # Execute migration SQL
        db_service.execute_raw_sql(sql_content)
        logger.info(f"Migration {migration_file} executed successfully")
        
    except Exception as e:
        logger.error(f"Migration {migration_file} failed: {str(e)}")
        raise DatabaseError(f"Migration failed: {str(e)}")


# Seed data utilities for development
def create_sample_data() -> None:
    """
    Create sample data for development and testing.
    Only available in debug mode.
    """
    if not settings.DEBUG:
        raise DatabaseError("Sample data creation only allowed in debug mode")
    
    from app.models.database import UserProfile, WorkExperience, Achievement
    from datetime import datetime, timedelta
    
    try:
        with db_service.get_session() as session:
            # Check if sample data already exists
            existing_user = session.query(UserProfile).filter_by(
                user_id="sample_user_001"
            ).first()
            
            if existing_user:
                logger.info("Sample data already exists")
                return
            
            # Create sample user profile
            sample_user = UserProfile(
                user_id="sample_user_001",
                full_name="John Smith",
                email="john.smith@example.com",
                phone="+1 (555) 123-4567",
                linkedin_url="https://linkedin.com/in/johnsmith",
                location="New York, NY",
                target_industries=["Technology", "Finance"],
                career_level="senior"
            )
            session.add(sample_user)
            session.flush()  # Get the ID
            
            # Create sample work experience
            sample_job = WorkExperience(
                profile_id=sample_user.id,
                company_name="TechCorp Inc",
                position_title="Senior Software Engineer",
                employment_type="full-time",
                start_date=datetime.now() - timedelta(days=730),  # 2 years ago
                end_date=datetime.now() - timedelta(days=365),    # 1 year ago
                location="San Francisco, CA",
                company_size="large",
                industry="Technology",
                role_summary="Led development of scalable web applications using modern technologies"
            )
            session.add(sample_job)
            session.flush()
            
            # Create sample achievements
            sample_achievements = [
                Achievement(
                    profile_id=sample_user.id,
                    experience_id=sample_job.id,
                    achievement_text="Led development team of 8 engineers to deliver critical product features ahead of schedule",
                    achievement_category="leadership",
                    impact_level=9,
                    business_function="engineering",
                    quantified_metrics={"team_size": 8, "schedule_improvement": "2 weeks early"},
                    keywords=["leadership", "team management", "software development"],
                    ats_keywords=["team lead", "project management", "agile development"],
                    skills_demonstrated=["Leadership", "Project Management", "Software Development"]
                ),
                Achievement(
                    profile_id=sample_user.id,
                    experience_id=sample_job.id,
                    achievement_text="Optimized database queries resulting in 40% performance improvement and $200K annual cost savings",
                    achievement_category="technical",
                    impact_level=8,
                    business_function="engineering",
                    quantified_metrics={"performance_improvement": 40, "cost_savings": 200000},
                    keywords=["database optimization", "performance", "cost reduction"],
                    ats_keywords=["database", "optimization", "performance tuning"],
                    skills_demonstrated=["Database Optimization", "Performance Analysis", "Cost Management"]
                )
            ]
            
            for achievement in sample_achievements:
                session.add(achievement)
            
            session.commit()
            logger.info("Sample data created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create sample data: {str(e)}")
        raise DatabaseError(f"Sample data creation failed: {str(e)}")