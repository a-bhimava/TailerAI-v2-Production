# Persistent Storage Architecture for TailerAI v2.0

**Document Status:** Active | **Version:** 1.0 | **Date:** July 17, 2025  
**Author:** TailerAI Architecture Team  
**Purpose:** Comprehensive technical architecture for persistent data storage using Google Cloud SQL  
**Scope:** Database layer, connection management, performance optimization, and scalability design

---

## 🏗️ Architecture Overview

### **Current vs. Target Architecture**

#### **Current Architecture (Ephemeral)**
```
┌─────────────────────────────────────┐
│        Google Cloud Run            │
│   ┌─────────────────────────────┐   │
│   │    TailerAI Container       │   │
│   │  ┌─────────────────────┐    │   │
│   │  │   SQLite Database   │    │   │  ❌ EPHEMERAL
│   │  │   (Container FS)    │    │   │     Data lost on:
│   │  └─────────────────────┘    │   │     • Container restart
│   └─────────────────────────────┘   │     • Deployment
└─────────────────────────────────────┘     • Scaling events
```

#### **Target Architecture (Persistent)**
```
┌─────────────────────────────────────┐
│        Google Cloud Run            │
│   ┌─────────────────────────────┐   │
│   │    TailerAI Container       │   │  ✅ PERSISTENT
│   │  ┌─────────────────────┐    │   │     Data persists through:
│   │  │  Application Logic  │────┼───┼────▶ • Container restarts
│   │  │  Connection Pool    │    │   │     • Deployments
│   │  └─────────────────────┘    │   │     • Scaling events
│   └─────────────────────────────┘   │     • Infrastructure changes
└─────────────────┬───────────────────┘
                  │ Cloud SQL Proxy
                  ▼
┌─────────────────────────────────────┐
│       Google Cloud SQL              │
│   ┌─────────────────────────────┐   │
│   │   PostgreSQL 13 Database    │   │
│   │  • Automated backups        │   │
│   │  • High availability        │   │
│   │  • Performance insights     │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🔧 Detailed Component Architecture

### **Data Layer Architecture**

#### **Cloud SQL PostgreSQL Instance**
```yaml
Configuration:
  Version: PostgreSQL 13
  Tier: db-f1-micro (1 vCPU, 0.6 GB RAM)
  Storage: 10GB SSD with auto-increase
  Region: us-central1
  Availability: Standard (upgradable to Regional HA)
  
Security:
  Network: Private IP (optional)
  Encryption: At rest and in transit
  Authentication: Password + IAM (dual mode)
  SSL: Required for all connections

Backup:
  Schedule: Daily at 3:00 AM UTC
  Retention: 30 days
  Point-in-time: 7 days
  Location: Regional (us-central1)

Performance:
  Connection Limit: 100 concurrent
  Query Insights: Enabled
  Performance Schema: Enabled
  Monitoring: Cloud SQL Insights
```

#### **Database Schema Architecture**
```
TailerAI Database Schema:
├── Core User Management
│   ├── user_profiles (primary user data)
│   ├── user_settings (preferences and config)
│   └── user_sessions (authentication state)
│
├── Master Dataset Engine
│   ├── work_experiences (employment history)
│   ├── achievements (accomplishments with metrics)
│   ├── education_entries (academic credentials)
│   ├── skills (technical and soft skills)
│   ├── projects (personal and professional)
│   └── certifications (professional credentials)
│
├── AI Processing Layer
│   ├── job_analyses (AI job description analysis)
│   ├── content_selections (AI content optimization)
│   ├── ats_optimizations (ATS compatibility analysis)
│   ├── content_enhancements (AI content improvements)
│   └── learning_events (system learning data)
│
├── Application Management
│   ├── job_applications (application tracking)
│   ├── application_outcomes (results and feedback)
│   ├── quality_assessments (content quality analysis)
│   └── ab_test_results (A/B testing data)
│
└── Operations and Analytics
    ├── resume_generations (PDF generation history)
    ├── template_usage (template analytics)
    ├── export_history (document export tracking)
    └── market_intelligence (market trend data)
```

### **Connection Architecture**

#### **Cloud Run to Cloud SQL Connection**
```
┌─────────────────────────────────────┐
│         Cloud Run Container         │
│                                     │
│  ┌─────────────────────────────┐    │
│  │     Application Layer       │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │  SQLAlchemy ORM     │    │    │
│  │  └─────────┬───────────┘    │    │
│  │            │                │    │
│  │  ┌─────────▼───────────┐    │    │
│  │  │  Connection Pool    │    │    │
│  │  │  • Pool Size: 20    │    │    │
│  │  │  • Max Overflow: 30 │    │    │
│  │  │  • Recycle: 1h      │    │    │
│  │  └─────────┬───────────┘    │    │
│  └────────────┼─────────────────┘    │
│               │                      │
│  ┌────────────▼─────────────────┐    │
│  │     Cloud SQL Proxy         │    │
│  │  • Automatic SSL             │    │
│  │  • IAM Authentication        │    │
│  │  • Connection Security       │    │
│  └────────────┬─────────────────┘    │
└───────────────┼─────────────────────┘
                │ Unix Socket
                │ /cloudsql/PROJECT:REGION:INSTANCE
                ▼
┌─────────────────────────────────────┐
│        Google Cloud SQL             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │   PostgreSQL Database       │    │
│  │  • Host: private-ip         │    │
│  │  • Port: 5432               │    │
│  │  • SSL: required            │    │
│  │  • Database: tailerai_prod  │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

#### **Connection Pool Configuration**
```python
# Optimized connection pool for Cloud SQL
class ConnectionConfig:
    # Basic pool settings
    pool_size: int = 20              # Base connections maintained
    max_overflow: int = 30           # Additional connections when needed
    pool_timeout: int = 30           # Max wait time for connection (seconds)
    pool_recycle: int = 3600         # Recycle connections after 1 hour
    pool_pre_ping: bool = True       # Test connections before use
    
    # PostgreSQL-specific settings
    connect_args = {
        'sslmode': 'require',        # Force SSL encryption
        'connect_timeout': 10,       # Initial connection timeout
        'application_name': 'tailerai-v2',  # For monitoring
        'options': '-c statement_timeout=30000'  # 30s query timeout
    }
    
    # Cloud SQL specific optimizations
    unix_socket_path = '/cloudsql/PROJECT_ID:us-central1:tailerai-db'
    
    # Performance monitoring
    echo_pool: bool = False          # Log connection pool activity
    echo: bool = False               # Log SQL queries (debug only)
```

---

## 📊 Performance Architecture

### **Database Performance Optimization**

#### **Indexing Strategy**
```sql
-- Primary Performance Indexes
CREATE INDEX CONCURRENTLY idx_user_profiles_email ON user_profiles(email);
CREATE INDEX CONCURRENTLY idx_user_profiles_active ON user_profiles(is_active) WHERE is_active = true;

-- Master Dataset Query Optimization
CREATE INDEX CONCURRENTLY idx_work_exp_user_dates ON work_experiences(user_id, start_date DESC, end_date DESC);
CREATE INDEX CONCURRENTLY idx_achievements_user_impact ON achievements(user_id, impact_level DESC);
CREATE INDEX CONCURRENTLY idx_skills_user_category ON skills(user_id, category, proficiency_level DESC);

-- AI Analysis Performance
CREATE INDEX CONCURRENTLY idx_job_analysis_created ON job_analyses(created_at DESC);
CREATE INDEX CONCURRENTLY idx_content_selection_score ON content_selections(relevance_score DESC);

-- JSONB Performance (PostgreSQL-specific)
CREATE INDEX CONCURRENTLY idx_achievements_keywords_gin ON achievements USING GIN ((keywords::jsonb));
CREATE INDEX CONCURRENTLY idx_job_requirements_gin ON job_analyses USING GIN ((requirements::jsonb));

-- Full-text Search Optimization
CREATE INDEX CONCURRENTLY idx_work_exp_description_fts ON work_experiences USING GIN (to_tsvector('english', description));
CREATE INDEX CONCURRENTLY idx_achievements_desc_fts ON achievements USING GIN (to_tsvector('english', description));
```

#### **Query Performance Patterns**
```python
# Optimized query patterns for common operations

# 1. User Dashboard Data (single query with joins)
user_dashboard_query = """
SELECT 
    up.username, up.email, up.created_at,
    COUNT(DISTINCT we.id) as work_experience_count,
    COUNT(DISTINCT a.id) as achievement_count,
    COUNT(DISTINCT s.id) as skill_count,
    MAX(rg.created_at) as last_resume_generated
FROM user_profiles up
LEFT JOIN work_experiences we ON up.id = we.user_id
LEFT JOIN achievements a ON up.id = a.user_id
LEFT JOIN skills s ON up.id = s.user_id
LEFT JOIN resume_generations rg ON up.id = rg.user_id
WHERE up.id = :user_id AND up.is_active = true
GROUP BY up.id, up.username, up.email, up.created_at
"""

# 2. Resume Content Selection (optimized for AI processing)
content_selection_query = """
WITH ranked_achievements AS (
    SELECT a.*, 
           ROW_NUMBER() OVER (PARTITION BY a.user_id ORDER BY a.impact_level DESC, a.created_at DESC) as rank
    FROM achievements a
    WHERE a.user_id = :user_id
),
recent_experience AS (
    SELECT we.*
    FROM work_experiences we
    WHERE we.user_id = :user_id
    ORDER BY we.start_date DESC, we.end_date DESC NULLS FIRST
    LIMIT 3
)
SELECT * FROM ranked_achievements WHERE rank <= 10
UNION ALL
SELECT * FROM recent_experience;
"""

# 3. Job Analysis with Caching
job_analysis_cached_query = """
SELECT ja.*, cs.relevance_score, cs.selected_content
FROM job_analyses ja
LEFT JOIN content_selections cs ON ja.id = cs.job_analysis_id
WHERE ja.job_description_hash = :job_hash
  AND ja.created_at > NOW() - INTERVAL '24 hours'
ORDER BY ja.created_at DESC
LIMIT 1;
"""
```

### **Caching Architecture**

#### **Application-Level Caching**
```python
# Multi-layer caching strategy
class CacheArchitecture:
    # Level 1: In-memory caching (per container)
    local_cache = {
        'user_profiles': TTLCache(maxsize=1000, ttl=300),  # 5 minutes
        'master_dataset': TTLCache(maxsize=500, ttl=600),  # 10 minutes
        'job_analyses': TTLCache(maxsize=200, ttl=1800),   # 30 minutes
    }
    
    # Level 2: Database query result caching
    sqlalchemy_cache = {
        'cache_expiry': 300,     # 5 minutes for most queries
        'cache_size': 10000,     # Maximum cached queries
        'cache_prefix': 'tailerai_v2',
    }
    
    # Level 3: Cloud SQL query cache (automatic)
    cloud_sql_cache = {
        'query_cache_size': '256MB',
        'query_cache_type': 'ON',
        'query_cache_limit': '1MB',
    }
```

#### **Database Connection Caching**
```python
# Connection pooling with intelligent caching
class ConnectionCacheManager:
    def __init__(self):
        self.pool_config = {
            # Aggressive connection reuse
            'pool_size': 20,
            'max_overflow': 30,
            'pool_recycle': 3600,    # 1 hour recycle
            'pool_pre_ping': True,   # Validate before use
            
            # Connection state caching
            'connect_args': {
                'server_side_cursors': False,  # Client-side for better caching
                'prepared_statement_cache_size': 100,
                'statement_cache_size': 50,
            }
        }
```

---

## 🔄 Scalability Architecture

### **Horizontal Scaling Design**

#### **Multi-Instance Architecture**
```
┌─────────────────────────────────────┐
│         Load Balancer               │
│      (Cloud Run Automatic)         │
└─────────┬───────────────────────────┘
          │
    ┌─────┴─────┬─────────────┬─────────────┐
    │           │             │             │
    ▼           ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐   ┌─────────┐
│Instance │ │Instance │ │Instance │...│Instance │
│   #1    │ │   #2    │ │   #3    │   │  #N     │
└─────┬───┘ └─────┬───┘ └─────┬───┘   └─────┬───┘
      │           │           │             │
      └─────┬─────┴─────┬─────┴─────────────┘
            │           │
            ▼           ▼
    ┌───────────────────────────────────────┐
    │       Shared Cloud SQL Database       │
    │     • Connection pooling              │
    │     • Automatic failover              │
    │     • Read replicas (future)          │
    └───────────────────────────────────────┘
```

#### **Connection Pool Scaling Strategy**
```python
# Dynamic connection pool sizing based on instance count
class ScalableConnectionPool:
    def __init__(self):
        # Base configuration per instance
        self.base_pool_size = 10
        self.base_max_overflow = 15
        
        # Scale based on expected concurrent instances
        self.max_instances = int(os.getenv('CLOUD_RUN_MAX_INSTANCES', 10))
        
        # Calculate optimal pool size
        self.pool_size = min(20, self.base_pool_size)
        self.max_overflow = min(30, self.base_max_overflow)
        
        # Ensure total connections don't exceed Cloud SQL limits
        max_db_connections = 100  # Cloud SQL limit
        estimated_instances = min(5, self.max_instances)  # Conservative estimate
        
        if (self.pool_size + self.max_overflow) * estimated_instances > max_db_connections:
            # Reduce pool size to prevent connection exhaustion
            self.pool_size = max_db_connections // (estimated_instances * 2)
            self.max_overflow = self.pool_size
```

### **Performance Scaling Roadmap**

#### **Phase 1: Basic Scalability (Current)**
```yaml
Capacity: 0-100 users
Infrastructure:
  Cloud SQL: db-f1-micro (1 vCPU, 0.6GB RAM)
  Cloud Run: 0-10 instances (2 CPU, 2GB RAM each)
  Storage: 10GB SSD
  Connections: 20 per instance, max 100 total

Expected Performance:
  Response Time: <100ms average
  Throughput: 100 requests/second
  Concurrent Users: 50-100
```

#### **Phase 2: Growth Scaling (Future)**
```yaml
Capacity: 100-1000 users
Infrastructure:
  Cloud SQL: db-n1-standard-1 (1 vCPU, 3.75GB RAM)
  Cloud Run: 0-50 instances
  Storage: 50GB SSD
  Connections: 15 per instance, max 200 total
  Read Replicas: 1 for read-heavy operations

Optimizations:
  - Read replica for dashboard queries
  - Connection pool optimization
  - Query performance tuning
  - Advanced caching layer
```

#### **Phase 3: Enterprise Scaling (Future)**
```yaml
Capacity: 1000+ users
Infrastructure:
  Cloud SQL: db-n1-standard-2 (2 vCPU, 7.5GB RAM)
  High Availability: Regional configuration
  Cloud Run: 0-100 instances
  Storage: 100GB SSD with auto-scaling
  Read Replicas: 2-3 for read distribution

Advanced Features:
  - Multi-region deployment
  - Advanced connection pooling (PgBouncer)
  - Partitioned tables for large datasets
  - Advanced monitoring and alerting
```

---

## 🛡️ Security Architecture

### **Data Security Layers**

#### **Network Security**
```
Security Layer 1: Network Isolation
┌─────────────────────────────────────┐
│         VPC Network (Optional)      │
│  ┌─────────────────────────────┐    │
│  │      Private Subnet         │    │
│  │  ┌─────────────────────┐    │    │
│  │  │   Cloud Run         │    │    │
│  │  │   (Private IP)      │────┼────┼───▶ Private Service Connect
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
                  │
                  ▼ Private IP Connection
┌─────────────────────────────────────┐
│      Cloud SQL Private IP          │
│  • No public IP exposure           │
│  • VPC-native connectivity         │
│  • Firewall rules protection       │
└─────────────────────────────────────┘
```

#### **Authentication and Authorization**
```python
# Multi-layer authentication architecture
class SecurityArchitecture:
    # Layer 1: Cloud SQL Authentication
    database_auth = {
        'method': 'dual',  # Password + IAM
        'ssl_mode': 'require',
        'cert_validation': True,
        'iam_service_account': 'tailerai-v2-sa@PROJECT.iam.gserviceaccount.com'
    }
    
    # Layer 2: Application Authentication
    app_auth = {
        'jwt_tokens': True,
        'session_management': True,
        'rate_limiting': True,
        'audit_logging': True
    }
    
    # Layer 3: Data Encryption
    encryption = {
        'at_rest': 'AES-256',          # Cloud SQL automatic
        'in_transit': 'TLS 1.2+',     # SSL connections
        'application': 'bcrypt',       # Password hashing
        'secrets': 'Secret Manager'    # API keys and tokens
    }
```

#### **Data Access Controls**
```sql
-- Database-level security policies
-- Row-level security for multi-tenant data isolation
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_experiences ENABLE ROW LEVEL SECURITY;
ALTER TABLE achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE education_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own data
CREATE POLICY user_data_isolation_policy ON user_profiles
    FOR ALL TO application_role
    USING (id = current_setting('app.current_user_id')::integer);

CREATE POLICY work_experience_isolation_policy ON work_experiences
    FOR ALL TO application_role
    USING (user_id = current_setting('app.current_user_id')::integer);

-- Similar policies for all user-specific tables...

-- Database roles and permissions
CREATE ROLE application_role;
GRANT CONNECT ON DATABASE tailerai_production TO application_role;
GRANT USAGE ON SCHEMA public TO application_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO application_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO application_role;
```

---

## 📊 Monitoring Architecture

### **Multi-Level Monitoring**

#### **Database Monitoring**
```yaml
Cloud SQL Monitoring:
  Metrics:
    - CPU utilization
    - Memory usage
    - Storage usage and growth
    - Connection count
    - Query performance
    - Replication lag (if applicable)
  
  Alerts:
    - CPU > 80% for 5 minutes
    - Memory > 90% for 2 minutes
    - Storage > 85% used
    - Connection count > 80% of limit
    - Slow query detection (>1 second)
  
  Query Insights:
    - Top queries by execution time
    - Top queries by CPU usage
    - Lock contention analysis
    - Index usage statistics
```

#### **Application Monitoring**
```python
# Application performance monitoring
class MonitoringArchitecture:
    # Database connection monitoring
    connection_metrics = {
        'pool_size': 'current_pool_size',
        'overflow_count': 'overflow_connections',
        'pool_timeout_count': 'connection_timeouts',
        'connection_errors': 'database_connection_errors'
    }
    
    # Query performance monitoring
    query_metrics = {
        'query_duration': 'histogram',
        'query_count': 'counter',
        'slow_query_count': 'counter',  # >100ms
        'failed_query_count': 'counter'
    }
    
    # Business metrics
    business_metrics = {
        'user_registrations': 'counter',
        'resume_generations': 'counter',
        'api_response_time': 'histogram',
        'active_users': 'gauge'
    }
```

#### **Health Check Architecture**
```python
# Comprehensive health checking
class HealthCheckSystem:
    async def database_health_check(self):
        """Check database connectivity and performance"""
        try:
            # Test basic connectivity
            async with self.db_service.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
            
            # Test query performance
            start_time = time.time()
            async with self.db_service.get_session() as session:
                await session.execute(text("SELECT COUNT(*) FROM user_profiles"))
            query_time = time.time() - start_time
            
            # Check connection pool health
            pool_status = self.db_service.engine.pool.status()
            
            return {
                "status": "healthy",
                "query_time_ms": round(query_time * 1000, 2),
                "pool_size": pool_status.pool_size,
                "checked_out": pool_status.checked_out,
                "overflow": pool_status.overflow,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
```

---

## 🔄 Backup and Disaster Recovery

### **Backup Strategy Architecture**

#### **Automated Backup Configuration**
```yaml
Primary Backups:
  Schedule: Daily at 3:00 AM UTC
  Retention: 30 days
  Type: Full database backup
  Location: Regional (us-central1)
  Encryption: Google-managed keys

Point-in-Time Recovery:
  Availability: 7 days
  Granularity: Per second
  Recovery Time: 1-4 hours
  Recovery Point: Any point within 7 days

Binary Logging:
  Enabled: Yes
  Retention: 7 days
  Purpose: Point-in-time recovery
  Storage: Included in backup costs
```

#### **Disaster Recovery Architecture**
```
Primary Region (us-central1):
┌─────────────────────────────────────┐
│        Production Instance          │
│  ┌─────────────────────────────┐    │
│  │   PostgreSQL Database       │    │
│  │   • Auto backups enabled    │    │
│  │   • Binary logging on       │    │
│  │   • Monitoring active       │    │
│  └─────────────────────────────┘    │
└─────────────────┬───────────────────┘
                  │
                  ▼ Backup Replication
┌─────────────────────────────────────┐
│         Backup Storage              │
│  • Cross-region replication        │
│  • 30-day retention                │
│  • Encrypted storage               │
│  • Automated testing               │
└─────────────────────────────────────┘

Disaster Recovery (if needed):
┌─────────────────────────────────────┐
│      Secondary Region               │
│  ┌─────────────────────────────┐    │
│  │   Recovery Instance         │    │
│  │   • Created from backup     │    │
│  │   • Manual activation       │    │
│  │   • RTO: 2-4 hours          │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### **Recovery Procedures**
```bash
# Disaster recovery procedures

# 1. Point-in-time recovery (for data corruption)
gcloud sql backups restore $BACKUP_ID \
    --restore-instance=$INSTANCE_NAME \
    --backup-instance=$INSTANCE_NAME

# 2. Create new instance from backup (for complete disaster)
gcloud sql instances clone $SOURCE_INSTANCE $NEW_INSTANCE \
    --point-in-time='2025-07-17T10:30:00.000Z'

# 3. Cross-region disaster recovery
gcloud sql instances create $DR_INSTANCE \
    --source-instance=$SOURCE_INSTANCE \
    --source-instance-region=$SOURCE_REGION \
    --region=$DR_REGION
```

---

## 📈 Future Architecture Evolution

### **Phase 1: Current Implementation (Months 1-3)**
- ✅ Basic Cloud SQL PostgreSQL
- ✅ Single-instance database
- ✅ Standard backup and monitoring
- ✅ Connection pooling optimization

### **Phase 2: Performance Enhancement (Months 4-6)**
- 📋 Read replica implementation
- 📋 Advanced caching layer (Redis)
- 📋 Query optimization and partitioning
- 📋 Enhanced monitoring and alerting

### **Phase 3: High Availability (Months 7-12)**
- 📋 Regional high availability
- 📋 Cross-region read replicas
- 📋 Advanced disaster recovery
- 📋 Multi-zone deployment

### **Phase 4: Global Scale (Year 2)**
- 📋 Multi-region deployment
- 📋 Global load balancing
- 📋 Advanced data partitioning
- 📋 Microservices architecture evolution

---

**Architecture Status**: ✅ **APPROVED FOR IMPLEMENTATION**  
**Implementation Readiness**: Ready for Phase 1 deployment  
**Next Steps**: Execute deployment following implementation guides  
**Evolution Path**: Continuous improvement based on usage patterns and growth