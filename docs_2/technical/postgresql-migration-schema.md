# PostgreSQL Migration Schema for TailerAI v2.0

**Document Status:** Active | **Version:** 1.0 | **Date:** July 17, 2025  
**Author:** TailerAI Database Team  
**Purpose:** Technical specification for migrating database schema from SQLite to PostgreSQL  
**Prerequisites:** Existing SQLAlchemy models in app/models/database.py

---

## 📋 Migration Overview

### **Migration Strategy**
- **Source**: SQLite database (ephemeral storage)
- **Target**: PostgreSQL 13 on Google Cloud SQL
- **Method**: SQLAlchemy ORM-based schema migration
- **Data**: Fresh deployment (no existing data to migrate)

### **Schema Compatibility**
- ✅ **SQLAlchemy Models**: Existing models compatible with PostgreSQL
- ✅ **Data Types**: All SQLite types map cleanly to PostgreSQL
- ✅ **Relationships**: Foreign key relationships preserved
- ✅ **Indexes**: Optimized for PostgreSQL performance

---

## 🗃️ Database Schema Analysis

### **Current SQLAlchemy Models (Compatible)**
```python
# From app/models/database.py - All models are PostgreSQL-compatible

Core User Models:
├── UserProfile (Primary user information)
├── UserSettings (User preferences and configuration)
└── UserSession (Session management)

Master Dataset Models:
├── WorkExperience (Employment history)
├── Achievement (Individual accomplishments)
├── EducationEntry (Academic credentials)
├── Skill (Technical and soft skills)
├── Project (Personal and professional projects)
└── Certification (Professional certifications)

AI and Analysis Models:
├── JobAnalysis (AI-powered job description analysis)
├── ContentSelection (AI content selection results)
├── ATSOptimization (ATS compatibility analysis)
├── ContentEnhancement (AI content improvements)
└── LearningEvent (System learning and optimization)

Application and Tracking Models:
├── JobApplication (Job application tracking)
├── ApplicationOutcome (Application results)
├── QualityAssessment (Content quality analysis)
├── ABTestResult (A/B testing results)
└── MarketIntelligence (Market trend analysis)

Resume Generation Models:
├── ResumeGeneration (PDF generation tracking)
├── TemplateUsage (Template usage statistics)
└── ExportHistory (Export and download history)
```

### **SQLite to PostgreSQL Type Mappings**
```sql
-- Automatic SQLAlchemy Type Conversions
SQLite Type          → PostgreSQL Type
-------------------- → ------------------
INTEGER              → INTEGER
TEXT                 → TEXT / VARCHAR
REAL                 → DOUBLE PRECISION
BLOB                 → BYTEA
BOOLEAN              → BOOLEAN
DATETIME             → TIMESTAMP
JSON                 → JSONB (enhanced)
```

---

## 🔧 Migration Implementation

### **Step 1: Database Connection Configuration**
```python
# app/config/settings.py - Enhanced for PostgreSQL
class Settings(BaseSettings):
    # Database settings with PostgreSQL optimization
    database_url: str = Field(
        default="sqlite:///./data/database/tailer_v2.db",
        env="DATABASE_URL"
    )
    
    # PostgreSQL-specific connection settings
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    db_pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
    
    # Cloud SQL specific
    cloud_sql_instance: str = Field(default="", env="CLOUD_SQL_INSTANCE")
```

### **Step 2: Enhanced Database Service for PostgreSQL**
```python
# app/services/database_service.py - PostgreSQL optimizations
class DatabaseService:
    def __init__(self):
        self.settings = get_settings()
        
        # PostgreSQL-optimized engine configuration
        engine_args = {
            'echo': self.settings.debug,
            'pool_pre_ping': self.settings.db_pool_pre_ping,
            'pool_recycle': self.settings.db_pool_recycle,
        }
        
        # Add PostgreSQL-specific settings
        if 'postgresql' in self.settings.database_url:
            engine_args.update({
                'pool_size': self.settings.db_pool_size,
                'max_overflow': self.settings.db_max_overflow,
                'pool_timeout': self.settings.db_pool_timeout,
                'connect_args': {
                    'sslmode': 'require',
                    'connect_timeout': 10,
                    'application_name': 'tailerai-v2',
                }
            })
        
        self.engine = create_engine(self.settings.database_url, **engine_args)
    
    async def create_tables(self):
        """Create all tables with PostgreSQL optimizations"""
        async with self.engine.begin() as conn:
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Create PostgreSQL-specific indexes
            await self._create_postgresql_indexes(conn)
    
    async def _create_postgresql_indexes(self, conn):
        """Create PostgreSQL-specific performance indexes"""
        indexes = [
            # User-related indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_profile_email ON user_profiles(email)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_profile_created ON user_profiles(created_at)",
            
            # Master dataset indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_experience_user_id ON work_experiences(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_education_user_id ON education_entries(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_skills_user_id ON skills(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_user_id ON projects(user_id)",
            
            # Performance indexes for queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_experience_dates ON work_experiences(start_date, end_date)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_achievements_impact ON achievements(impact_level)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_skills_proficiency ON skills(proficiency_level)",
            
            # AI analysis indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_analysis_created ON job_analyses(created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_selection_job ON content_selections(job_analysis_id)",
            
            # JSONB indexes for flexible queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_achievements_keywords_gin ON achievements USING GIN ((keywords::jsonb))",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_analysis_requirements_gin ON job_analyses USING GIN ((requirements::jsonb))",
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
                logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {e}")
```

### **Step 3: PostgreSQL-Optimized Model Enhancements**
```python
# Enhancements to existing models for PostgreSQL
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import Index

class WorkExperience(Base):
    __tablename__ = "work_experiences"
    
    # Existing fields...
    
    # PostgreSQL-specific optimizations
    __table_args__ = (
        Index('idx_work_exp_user_company', 'user_id', 'company'),
        Index('idx_work_exp_date_range', 'start_date', 'end_date'),
        {'schema': 'public'}  # Explicit schema for PostgreSQL
    )

class Achievement(Base):
    __tablename__ = "achievements"
    
    # Use JSONB for better performance in PostgreSQL
    keywords: Optional[List[str]] = Column(
        JSONB if 'postgresql' in str(database_url) else JSON,
        nullable=True
    )
    
    # PostgreSQL-specific indexes
    __table_args__ = (
        Index('idx_achievements_keywords_gin', 'keywords', postgresql_using='gin'),
        Index('idx_achievements_impact_user', 'impact_level', 'user_id'),
    )

class JobAnalysis(Base):
    __tablename__ = "job_analyses"
    
    # Enhanced JSONB fields for PostgreSQL
    requirements: Optional[Dict] = Column(
        JSONB if 'postgresql' in str(database_url) else JSON,
        nullable=True
    )
    
    keywords_analysis: Optional[Dict] = Column(
        JSONB if 'postgresql' in str(database_url) else JSON,
        nullable=True
    )
```

---

## 📊 Performance Optimizations

### **PostgreSQL-Specific Indexes**
```sql
-- Core performance indexes for frequent queries

-- User authentication and lookup
CREATE INDEX CONCURRENTLY idx_user_profiles_email_active 
ON user_profiles(email) WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_user_profiles_created_date 
ON user_profiles(created_at DESC);

-- Master dataset performance
CREATE INDEX CONCURRENTLY idx_work_experiences_user_current 
ON work_experiences(user_id, end_date DESC NULLS FIRST);

CREATE INDEX CONCURRENTLY idx_achievements_user_impact 
ON achievements(user_id, impact_level DESC, created_at DESC);

CREATE INDEX CONCURRENTLY idx_education_user_graduation 
ON education_entries(user_id, graduation_date DESC NULLS FIRST);

-- Multi-column indexes for complex queries
CREATE INDEX CONCURRENTLY idx_content_selections_job_score 
ON content_selections(job_analysis_id, relevance_score DESC);

CREATE INDEX CONCURRENTLY idx_job_applications_user_status_date 
ON job_applications(user_id, status, applied_date DESC);

-- JSONB performance indexes
CREATE INDEX CONCURRENTLY idx_achievements_keywords_gin 
ON achievements USING GIN ((keywords::jsonb));

CREATE INDEX CONCURRENTLY idx_job_analysis_requirements_gin 
ON job_analyses USING GIN ((requirements::jsonb));

CREATE INDEX CONCURRENTLY idx_skills_categories_gin 
ON skills USING GIN ((categories::jsonb));

-- Full-text search indexes
CREATE INDEX CONCURRENTLY idx_work_experiences_description_fts 
ON work_experiences USING GIN (to_tsvector('english', description));

CREATE INDEX CONCURRENTLY idx_achievements_description_fts 
ON achievements USING GIN (to_tsvector('english', description));
```

### **Connection Pool Configuration**
```python
# Optimized connection pool for Cloud SQL
DATABASE_CONFIG = {
    'pool_size': 20,              # Base connections in pool
    'max_overflow': 30,           # Additional connections beyond pool_size
    'pool_timeout': 30,           # Max wait time for connection
    'pool_recycle': 3600,         # Recycle connections every hour
    'pool_pre_ping': True,        # Validate connections before use
    
    # Cloud SQL specific settings
    'connect_args': {
        'sslmode': 'require',     # Force SSL for security
        'connect_timeout': 10,    # Connection timeout
        'application_name': 'tailerai-v2',  # For monitoring
        'options': '-c statement_timeout=30000'  # 30 second query timeout
    }
}
```

---

## 🔄 Migration Procedures

### **Fresh Schema Creation (Recommended)**
```python
# Migration script for fresh PostgreSQL deployment
async def create_fresh_schema():
    """Create fresh schema in PostgreSQL"""
    try:
        # Create database service
        db_service = DatabaseService()
        
        # Create all tables
        await db_service.create_tables()
        
        # Create PostgreSQL-specific indexes
        await db_service.create_performance_indexes()
        
        # Create database functions and triggers
        await db_service.create_postgresql_functions()
        
        # Verify schema integrity
        await db_service.verify_schema()
        
        logger.info("✅ PostgreSQL schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        return False
```

### **Data Migration (If Needed)**
```python
# Migration script for existing data (if any)
async def migrate_existing_data():
    """Migrate data from SQLite to PostgreSQL"""
    try:
        # Connect to both databases
        sqlite_engine = create_engine("sqlite:///./data/database/tailer_v2.db")
        postgres_engine = create_engine(settings.database_url)
        
        # Get all table names
        tables = Base.metadata.tables.keys()
        
        for table_name in tables:
            logger.info(f"Migrating table: {table_name}")
            
            # Read from SQLite
            with sqlite_engine.connect() as sqlite_conn:
                data = pd.read_sql_table(table_name, sqlite_conn)
            
            # Write to PostgreSQL
            with postgres_engine.connect() as postgres_conn:
                data.to_sql(
                    table_name, 
                    postgres_conn, 
                    if_exists='append',
                    index=False,
                    method='multi'  # Batch inserts for performance
                )
            
            logger.info(f"✅ Migrated {len(data)} rows from {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data migration failed: {e}")
        return False
```

### **Schema Validation**
```python
# Validation script to ensure migration success
async def validate_schema_migration():
    """Validate PostgreSQL schema matches expected structure"""
    try:
        db_service = DatabaseService()
        
        # Check table existence
        tables = await db_service.get_table_list()
        expected_tables = set(Base.metadata.tables.keys())
        
        missing_tables = expected_tables - set(tables)
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check indexes
        for table_name in expected_tables:
            indexes = await db_service.get_table_indexes(table_name)
            logger.info(f"✅ Table {table_name}: {len(indexes)} indexes")
        
        # Check constraints
        constraints = await db_service.get_foreign_key_constraints()
        logger.info(f"✅ Foreign key constraints: {len(constraints)}")
        
        # Test basic operations
        await db_service.test_crud_operations()
        
        logger.info("✅ Schema validation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema validation failed: {e}")
        return False
```

---

## 🧪 Testing Procedures

### **Database Connection Testing**
```python
async def test_database_connection():
    """Test PostgreSQL connection and basic operations"""
    try:
        db_service = DatabaseService()
        
        # Test connection
        async with db_service.get_session() as session:
            result = await session.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"✅ Connected to: {version}")
        
        # Test table access
        async with db_service.get_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM user_profiles;"))
            count = result.scalar()
            logger.info(f"✅ User profiles table accessible, count: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False
```

### **Performance Testing**
```python
async def test_query_performance():
    """Test PostgreSQL query performance"""
    try:
        db_service = DatabaseService()
        
        # Test query performance
        queries = [
            "SELECT COUNT(*) FROM user_profiles WHERE is_active = true",
            "SELECT * FROM work_experiences WHERE user_id = 1 ORDER BY start_date DESC LIMIT 10",
            "SELECT * FROM achievements WHERE keywords::jsonb ? 'python' LIMIT 10",
        ]
        
        for query in queries:
            start_time = time.time()
            async with db_service.get_session() as session:
                await session.execute(text(query))
            end_time = time.time()
            
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            logger.info(f"✅ Query executed in {duration:.2f}ms: {query[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return False
```

---

## 📋 Migration Checklist

### **Pre-Migration**
- [ ] **PostgreSQL Instance**: Cloud SQL instance created and accessible
- [ ] **Database Created**: Application database exists with correct settings
- [ ] **User Access**: Database user created with appropriate permissions
- [ ] **Network Access**: Cloud Run can connect to Cloud SQL
- [ ] **Environment Variables**: Database URL and connection settings configured

### **Schema Migration**
- [ ] **Tables Created**: All SQLAlchemy models successfully created
- [ ] **Indexes Applied**: Performance indexes created and operational
- [ ] **Constraints Verified**: Foreign key relationships working correctly
- [ ] **Functions Installed**: PostgreSQL-specific functions and triggers active

### **Application Integration**
- [ ] **Connection Pool**: Database connection pool configured and tested
- [ ] **ORM Operations**: SQLAlchemy CRUD operations working correctly
- [ ] **Query Performance**: Database queries performing within acceptable limits
- [ ] **Error Handling**: Database error handling working properly

### **Data Validation**
- [ ] **Schema Integrity**: All tables, indexes, and constraints present
- [ ] **CRUD Operations**: Create, read, update, delete operations functional
- [ ] **Relationship Integrity**: Foreign key relationships working correctly
- [ ] **Performance Baseline**: Query performance benchmarks established

### **Production Readiness**
- [ ] **Backup Configuration**: Automated backups enabled and tested
- [ ] **Monitoring Setup**: Database monitoring and alerting configured
- [ ] **Security Validation**: SSL connections and access controls verified
- [ ] **Disaster Recovery**: Recovery procedures documented and tested

---

## 🔧 Troubleshooting Common Issues

### **Connection Issues**
```bash
# Test Cloud SQL connectivity
gcloud sql connect tailerai-db --user=tailerai_user --database=tailerai_production

# Check Cloud Run Cloud SQL annotation
gcloud run services describe tailerai-v2 --region=us-central1 \
    --format="value(spec.template.metadata.annotations)"

# Verify service account permissions
gcloud projects get-iam-policy PROJECT_ID \
    --filter="bindings.members:*tailerai-v2-sa*"
```

### **Performance Issues**
```sql
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' 
AND n_distinct > 100;

-- Monitor query performance
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check connection pool status
SELECT count(*), state 
FROM pg_stat_activity 
GROUP BY state;
```

### **Schema Issues**
```sql
-- Verify table structure
\d+ user_profiles
\d+ work_experiences
\d+ achievements

-- Check indexes
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public';

-- Verify constraints
SELECT conname, contype, conrelid::regclass 
FROM pg_constraint 
WHERE connamespace = 'public'::regnamespace;
```

---

**Migration Status**: ✅ **READY FOR EXECUTION**  
**Dependencies**: Cloud SQL instance operational, application configured  
**Next Steps**: Execute migration following procedures in this document  
**Support**: Reference troubleshooting section for common migration issues