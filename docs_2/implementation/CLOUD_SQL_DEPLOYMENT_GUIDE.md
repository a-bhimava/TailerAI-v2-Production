# Cloud SQL Deployment Guide for TailerAI v2.0

**Document Status:** Active | **Version:** 1.0 | **Date:** July 17, 2025  
**Author:** TailerAI Infrastructure Team  
**Purpose:** Detailed deployment procedures for Google Cloud SQL PostgreSQL implementation  
**Prerequisites:** DATA_PERSISTENCE_IMPLEMENTATION_GUIDE.md completed

---

## 📋 Deployment Overview

### **Deployment Architecture**
```
New Parallel Deployment:
┌─────────────────────────────────────┐
│     Original Production             │
│   tailerai-34742245611              │
│   ├─ SQLite (ephemeral)             │
│   ├─ Cloud Run Service              │
│   └─ Users: [current traffic]       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│     New Persistent Deployment      │
│   tailerai-persistent-v2           │
│   ├─ PostgreSQL (Cloud SQL)        │
│   ├─ Cloud Run Service             │
│   └─ Users: [testing/migration]    │
└─────────────────────────────────────┘
```

### **Deployment Principles**
- ✅ **Zero Risk**: Original service remains untouched
- ✅ **Comprehensive Testing**: Full validation before user migration
- ✅ **Rollback Ready**: Immediate fallback to original service if needed
- ✅ **Performance Validated**: Benchmarked against current service

---

## 🎯 Pre-Deployment Requirements

### **Required Permissions**
```bash
# Google Cloud IAM roles needed for deployment
Required Roles:
├── Project Creator (for new project setup)
├── Cloud SQL Admin (for database management)
├── Cloud Run Admin (for service deployment)
├── Service Account Admin (for IAM configuration)
├── Secret Manager Admin (for secrets management)
└── Monitoring Admin (for observability setup)
```

### **Required Information**
- [ ] **Google Cloud Billing Account**: Active billing account ID
- [ ] **API Keys**: Gemini API key and application secrets
- [ ] **Domain Requirements**: DNS access if custom domain needed
- [ ] **Network Configuration**: VPC requirements if applicable

### **Tools Verification**
```bash
# Verify required tools are installed and authenticated
gcloud --version          # Google Cloud SDK
docker --version          # Docker for container builds
curl --version            # For testing endpoints

# Verify authentication
gcloud auth list
gcloud auth application-default print-access-token
```

---

## 🚀 Deployment Phase 1: Project Infrastructure (60 minutes)

### **Step 1.1: Create and Configure New Project**

#### **Create Project via Console (Manual)**
1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. **Project Name**: `TailerAI Persistent v2`
4. **Project ID**: `tailerai-persistent-v2` (or auto-generated)
5. **Organization**: Select your organization
6. **Location**: Select billing account location
7. Click "Create"

#### **Configure Project via CLI**
```bash
# Set project variables
export NEW_PROJECT_ID="tailerai-persistent-v2"
export REGION="us-central1"
export ZONE="us-central1-a"

# Verify project exists and set as current
gcloud projects describe $NEW_PROJECT_ID
gcloud config set project $NEW_PROJECT_ID

# Set default regions
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
gcloud config set run/region $REGION

# Verify configuration
gcloud config list
```

### **Step 1.2: Enable APIs and Services**
```bash
# Core services for the application
gcloud services enable run.googleapis.com              # Cloud Run
gcloud services enable sqladmin.googleapis.com         # Cloud SQL
gcloud services enable cloudbuild.googleapis.com       # Cloud Build
gcloud services enable containerregistry.googleapis.com # Container Registry
gcloud services enable secretmanager.googleapis.com    # Secret Manager

# Monitoring and logging
gcloud services enable monitoring.googleapis.com       # Cloud Monitoring
gcloud services enable logging.googleapis.com          # Cloud Logging

# Optional: Additional services
gcloud services enable compute.googleapis.com          # Compute Engine (if VPC needed)
gcloud services enable servicenetworking.googleapis.com # Private Services Access

# Verify all APIs are enabled
gcloud services list --enabled --filter="name:(run OR sqladmin OR cloudbuild OR containerregistry OR secretmanager)"
```

### **Step 1.3: Create Service Account with Minimal Permissions**
```bash
# Create service account
gcloud iam service-accounts create tailerai-v2-sa \
    --description="TailerAI v2.0 Service Account for Persistent Storage" \
    --display-name="TailerAI v2.0 Persistent"

# Set service account variable
export SERVICE_ACCOUNT="tailerai-v2-sa@$NEW_PROJECT_ID.iam.gserviceaccount.com"

# Grant minimal required permissions
gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Optional: Monitoring permissions for production
gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/logging.logWriter"

# Verify permissions
gcloud projects get-iam-policy $NEW_PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT"
```

---

## 🗄️ Deployment Phase 2: Cloud SQL Setup (45 minutes)

### **Step 2.1: Create Cloud SQL Instance**
```bash
# Set database configuration
export DB_INSTANCE_NAME="tailerai-db"
export DB_NAME="tailerai_production"
export DB_USER="tailerai_user"

# Generate secure password (SAVE THIS!)
export DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "🔐 Database Password (SAVE THIS): $DB_PASSWORD"
echo "Password saved to: ./db_password.txt"
echo $DB_PASSWORD > ./db_password.txt

# Create Cloud SQL instance with optimal configuration
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --storage-auto-increase-limit=100GB \
    --backup-start-time=03:00 \
    --backup-location=$REGION \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --maintenance-release-channel=production \
    --deletion-protection \
    --no-assign-ip

# Wait for instance to be ready
echo "⏳ Waiting for instance to be ready..."
gcloud sql instances describe $DB_INSTANCE_NAME --format="value(state)"
```

### **Step 2.2: Configure Database and User**
```bash
# Create application database
gcloud sql databases create $DB_NAME \
    --instance=$DB_INSTANCE_NAME \
    --charset=UTF8 \
    --collation=en_US.UTF8

# Create database user with password
gcloud sql users create $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_PASSWORD

# Verify database setup
gcloud sql instances describe $DB_INSTANCE_NAME
gcloud sql databases list --instance=$DB_INSTANCE_NAME
gcloud sql users list --instance=$DB_INSTANCE_NAME
```

### **Step 2.3: Configure Security and Access**
```bash
# Enable IAM authentication (optional, for enhanced security)
gcloud sql instances patch $DB_INSTANCE_NAME \
    --database-flags=cloudsql.iam_authentication=on

# Create IAM database user for service account (optional)
gcloud sql users create $SERVICE_ACCOUNT \
    --instance=$DB_INSTANCE_NAME \
    --type=cloud_iam_service_account

# Configure connection settings for Cloud Run
export CONNECTION_NAME="$NEW_PROJECT_ID:$REGION:$DB_INSTANCE_NAME"
echo "🔗 Connection Name: $CONNECTION_NAME"

# Test database connectivity (optional)
gcloud sql connect $DB_INSTANCE_NAME \
    --user=$DB_USER \
    --database=$DB_NAME \
    --quiet
```

### **Step 2.4: Database Performance Configuration**
```bash
# Configure PostgreSQL for optimal performance
gcloud sql instances patch $DB_INSTANCE_NAME \
    --database-flags=shared_preload_libraries=pg_stat_statements,max_connections=100,shared_buffers=128MB

# Enable query performance insights
gcloud sql instances patch $DB_INSTANCE_NAME \
    --insights-config-query-insights-enabled \
    --insights-config-query-string-length=1024 \
    --insights-config-record-application-tags \
    --insights-config-record-client-address
```

---

## 🔐 Deployment Phase 3: Secret Management (20 minutes)

### **Step 3.1: Transfer Secrets from Original Project**

#### **Option A: Manual Secret Entry**
```bash
# Prompt for manual entry of secrets
echo "📝 Please provide the following secrets:"
echo -n "Gemini API Key: "; read -s GEMINI_API_KEY; echo
echo -n "Application Secret Key: "; read -s SECRET_KEY; echo
echo -n "JWT Secret Key: "; read -s JWT_SECRET_KEY; echo
```

#### **Option B: Copy from Original Project (if accessible)**
```bash
# Temporarily switch to original project
export ORIGINAL_PROJECT_ID="tailerai-34742245611"
gcloud config set project $ORIGINAL_PROJECT_ID

# Export secrets (if you have access)
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret="tailerai-gemini-api-key" 2>/dev/null || echo "MANUAL_ENTRY_REQUIRED")
export SECRET_KEY=$(gcloud secrets versions access latest --secret="tailerai-secret-key" 2>/dev/null || echo "MANUAL_ENTRY_REQUIRED")
export JWT_SECRET_KEY=$(gcloud secrets versions access latest --secret="tailerai-jwt-secret" 2>/dev/null || echo "MANUAL_ENTRY_REQUIRED")

# Switch back to new project
gcloud config set project $NEW_PROJECT_ID
```

### **Step 3.2: Create Secrets in New Project**
```bash
# Create database password secret
echo -n "$DB_PASSWORD" | gcloud secrets create tailerai-db-password \
    --data-file=- \
    --labels=app=tailerai,environment=production,type=database

# Create Gemini API key secret
echo -n "$GEMINI_API_KEY" | gcloud secrets create tailerai-gemini-api-key \
    --data-file=- \
    --labels=app=tailerai,environment=production,type=api

# Create application secret key
echo -n "$SECRET_KEY" | gcloud secrets create tailerai-secret-key \
    --data-file=- \
    --labels=app=tailerai,environment=production,type=application

# Create JWT secret key
echo -n "$JWT_SECRET_KEY" | gcloud secrets create tailerai-jwt-secret \
    --data-file=- \
    --labels=app=tailerai,environment=production,type=authentication

# Verify secrets were created
gcloud secrets list --filter="labels.app=tailerai"
```

### **Step 3.3: Configure Secret Access Permissions**
```bash
# Grant service account access to secrets
secrets=(
    "tailerai-db-password"
    "tailerai-gemini-api-key"
    "tailerai-secret-key"
    "tailerai-jwt-secret"
)

for secret in "${secrets[@]}"; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor"
    echo "✅ Granted access to $secret"
done

# Verify access permissions
for secret in "${secrets[@]}"; do
    gcloud secrets get-iam-policy $secret \
        --filter="bindings.members:$SERVICE_ACCOUNT" \
        --format="value(bindings.role)"
done
```

---

## 🔧 Deployment Phase 4: Application Deployment (40 minutes)

### **Step 4.1: Prepare Application Code**
```bash
# Navigate to project directory
cd /Users/aditya/Documents/Tailor/TailerAI-v2-Production

# Verify current directory and files
pwd
ls -la

# Check if PostgreSQL driver is in requirements
grep -q "psycopg2-binary" requirements.txt || echo "psycopg2-binary==2.9.9" >> requirements.txt

# Verify addition
tail -5 requirements.txt
```

### **Step 4.2: Build and Push Container**
```bash
# Configure Docker authentication for new project
gcloud auth configure-docker

# Build container with correct platform for Cloud Run
docker build --platform linux/amd64 \
    -t gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest \
    -t gcr.io/$NEW_PROJECT_ID/tailerai-v2:$(date +%Y%m%d-%H%M%S) \
    .

# Verify build completed successfully
docker images | grep gcr.io/$NEW_PROJECT_ID/tailerai-v2

# Push container to registry
docker push gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest

# Verify image is in registry
gcloud container images list --repository=gcr.io/$NEW_PROJECT_ID
gcloud container images list-tags gcr.io/$NEW_PROJECT_ID/tailerai-v2
```

### **Step 4.3: Deploy to Cloud Run**
```bash
# Set deployment variables
export SERVICE_NAME="tailerai-v2"
export IMAGE_URL="gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest"

# Deploy with comprehensive configuration
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URL \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SERVICE_ACCOUNT \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300s \
    --concurrency 100 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8080 \
    --add-cloudsql-instances $CONNECTION_NAME \
    --set-env-vars="ENVIRONMENT=production,DEBUG=False,HOST=0.0.0.0,PORT=8080,LOG_LEVEL=INFO,LATEX_ENGINE=pdflatex,LATEX_ENGINE_PATH=/usr/bin/pdflatex" \
    --set-env-vars="DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME" \
    --set-env-vars="CLOUD_SQL_INSTANCE=$CONNECTION_NAME,DB_POOL_SIZE=20,DB_MAX_OVERFLOW=30,DB_POOL_RECYCLE=3600" \
    --set-secrets="GEMINI_API_KEY=tailerai-gemini-api-key:latest,SECRET_KEY=tailerai-secret-key:latest,JWT_SECRET_KEY=tailerai-jwt-secret:latest"

# Get service URL
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"
echo $SERVICE_URL > ./service_url.txt
```

### **Step 4.4: Verify Deployment**
```bash
# Check service status
gcloud run services describe $SERVICE_NAME --region $REGION

# Test health endpoint
curl -f $SERVICE_URL/health

# Test with detailed response
curl -v $SERVICE_URL/health

# Check application logs
gcloud run services logs tail $SERVICE_NAME --region=$REGION

# Verify database connection in logs
gcloud run services logs read $SERVICE_NAME --region=$REGION --filter="severity>=INFO" --limit=50
```

---

## 🧪 Deployment Phase 5: Testing and Validation (30 minutes)

### **Step 5.1: Basic Health and Connectivity Tests**
```bash
# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -s $SERVICE_URL/health | jq .

# Test API documentation
echo "📚 Testing API documentation..."
curl -s $SERVICE_URL/docs -I | head -1

# Test main application endpoint
echo "🏠 Testing main application..."
curl -s $SERVICE_URL/ -I | head -1

# Test static file serving
echo "📁 Testing static files..."
curl -s $SERVICE_URL/static/css/style.css -I | head -1
```

### **Step 5.2: Database Functionality Tests**
```bash
# Test user registration (creates database record)
echo "👤 Testing user registration..."
curl -X POST $SERVICE_URL/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@tailerai-test.com",
        "password": "TestPassword123!",
        "username": "testuser"
    }' | jq .

# Test user login (reads from database)
echo "🔐 Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST $SERVICE_URL/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@tailerai-test.com&password=TestPassword123!")

echo $LOGIN_RESPONSE | jq .

# Extract access token for further testing
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token // empty')
echo "🎫 Access Token: ${ACCESS_TOKEN:0:20}..."
```

### **Step 5.3: Data Persistence Tests**
```bash
# Test data creation with authentication
if [ -n "$ACCESS_TOKEN" ]; then
    echo "📝 Testing data persistence..."
    
    # Create work experience entry
    curl -X POST $SERVICE_URL/api/v2/experience \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "company": "Test Company",
            "position": "Test Position",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "description": "Test work experience for persistence validation"
        }' | jq .
    
    # Verify data can be retrieved
    curl -s -X GET $SERVICE_URL/api/v2/experience \
        -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
else
    echo "⚠️ No access token available for authenticated tests"
fi
```

### **Step 5.4: Container Restart Test**
```bash
# Force container restart by redeploying same image
echo "🔄 Testing data persistence across container restart..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URL \
    --region $REGION \
    --quiet

# Wait for deployment to complete
sleep 30

# Test that health endpoint is back up
curl -f $SERVICE_URL/health

# Verify data persists after restart
if [ -n "$ACCESS_TOKEN" ]; then
    # Note: Token might be invalid after restart, would need new login in real test
    echo "🔍 Checking if data persisted after restart..."
    curl -s -X GET $SERVICE_URL/api/v2/experience \
        -H "Authorization: Bearer $ACCESS_TOKEN" | jq . || echo "Need to re-authenticate after restart"
fi
```

---

## 📊 Deployment Phase 6: Monitoring Setup (25 minutes)

### **Step 6.1: Create Monitoring Dashboard**
```bash
# Create monitoring dashboard for the service
cat > monitoring-dashboard.json << 'EOF'
{
  "displayName": "TailerAI v2.0 - Persistent Storage Dashboard",
  "labels": {
    "app": "tailerai",
    "version": "v2.0",
    "environment": "production"
  },
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cloud Run Request Count",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"tailerai-v2\"",
                  "metricType": "run.googleapis.com/request_count"
                }
              }
            }]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cloud SQL CPU Utilization",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"PROJECT_ID:tailerai-db\"",
                  "metricType": "cloudsql.googleapis.com/database/cpu/utilization"
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF

# Replace PROJECT_ID placeholder
sed -i "s/PROJECT_ID/$NEW_PROJECT_ID/g" monitoring-dashboard.json

# Create dashboard
gcloud monitoring dashboards create --config-from-file=monitoring-dashboard.json
```

### **Step 6.2: Set Up Alerting Policies**
```bash
# Create alert policy for service downtime
cat > alert-policy.json << 'EOF'
{
  "displayName": "TailerAI v2.0 - Service Health Alert",
  "conditions": [
    {
      "displayName": "Cloud Run Service Errors",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"tailerai-v2\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 5,
        "duration": "300s"
      }
    }
  ],
  "enabled": true,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF

# Create alert policy
gcloud alpha monitoring policies create --policy-from-file=alert-policy.json

# Clean up temporary files
rm monitoring-dashboard.json alert-policy.json
```

### **Step 6.3: Configure Log-based Metrics**
```bash
# Create log-based metric for database connection errors
gcloud logging metrics create database_connection_errors \
    --description="Database connection error count" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="tailerai-v2" AND severity>=ERROR AND jsonPayload.message:"database"'

# Create log-based metric for successful requests
gcloud logging metrics create successful_requests \
    --description="Successful API request count" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="tailerai-v2" AND httpRequest.status>=200 AND httpRequest.status<400'
```

---

## ✅ Deployment Validation Checklist

### **Infrastructure Validation**
- [ ] **Google Cloud Project**: New project created and configured
- [ ] **APIs Enabled**: All required APIs activated and functional
- [ ] **Service Account**: Created with minimal required permissions
- [ ] **IAM Policies**: Properly configured with least privilege access

### **Database Validation**
- [ ] **Cloud SQL Instance**: Running and accessible
- [ ] **Database Created**: Application database exists with correct encoding
- [ ] **User Access**: Database user created with appropriate permissions
- [ ] **Connection**: Cloud Run can connect to Cloud SQL
- [ ] **Performance**: Query performance insights enabled

### **Security Validation**
- [ ] **Secrets Management**: All secrets stored in Secret Manager
- [ ] **Access Control**: Service account has minimal required permissions
- [ ] **Network Security**: Private IP and SSL connections configured
- [ ] **Audit Logging**: Database and application audit logging enabled

### **Application Validation**
- [ ] **Container Build**: Successfully built and pushed to registry
- [ ] **Cloud Run Deployment**: Service deployed and responding
- [ ] **Health Checks**: Health endpoint returning successful responses
- [ ] **Database Connectivity**: Application successfully connecting to database
- [ ] **API Functionality**: Core API endpoints working correctly

### **Data Persistence Validation**
- [ ] **User Registration**: Can create user accounts (database writes)
- [ ] **Data Retrieval**: Can read user data (database reads)
- [ ] **Data Persistence**: Data survives container restarts
- [ ] **Resume Generation**: PDF generation works with persistent storage

### **Monitoring Validation**
- [ ] **Dashboard Created**: Monitoring dashboard operational
- [ ] **Metrics Flowing**: Both Cloud Run and Cloud SQL metrics visible
- [ ] **Alerting Configured**: Alert policies created and enabled
- [ ] **Log Aggregation**: Application logs flowing to Cloud Logging

---

## 🚨 Troubleshooting Guide

### **Common Deployment Issues**

#### **Cloud SQL Connection Issues**
```bash
# Symptoms: Application can't connect to database
# Check 1: Verify Cloud SQL instance is running
gcloud sql instances describe $DB_INSTANCE_NAME

# Check 2: Verify Cloud Run has Cloud SQL connection annotation
gcloud run services describe $SERVICE_NAME --region=$REGION \
    --format="value(spec.template.metadata.annotations.run\.googleapis\.com\/cloudsql-instances)"

# Check 3: Test connectivity from Cloud Shell
gcloud sql connect $DB_INSTANCE_NAME --user=$DB_USER --database=$DB_NAME

# Fix: Re-deploy with correct Cloud SQL connection
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URL \
    --add-cloudsql-instances $CONNECTION_NAME \
    --region $REGION
```

#### **Secret Access Issues**
```bash
# Symptoms: Application can't access secrets
# Check 1: Verify secrets exist
gcloud secrets list --filter="labels.app=tailerai"

# Check 2: Verify service account has access
gcloud secrets get-iam-policy tailerai-gemini-api-key \
    --filter="bindings.members:$SERVICE_ACCOUNT"

# Check 3: Test secret access
gcloud secrets versions access latest --secret="tailerai-gemini-api-key"

# Fix: Grant access if missing
gcloud secrets add-iam-policy-binding tailerai-gemini-api-key \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
```

#### **Container Build Issues**
```bash
# Symptoms: Docker build or push failures
# Check 1: Verify Docker authentication
gcloud auth configure-docker

# Check 2: Check available disk space
df -h

# Check 3: Verify platform specification
docker build --platform linux/amd64 -t test-image .

# Fix: Clean up Docker cache and rebuild
docker system prune -f
docker build --no-cache --platform linux/amd64 -t gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest .
```

#### **Performance Issues**
```bash
# Symptoms: Slow response times or timeouts
# Check 1: Monitor database performance
gcloud sql operations list --instance=$DB_INSTANCE_NAME

# Check 2: Check Cloud Run metrics
gcloud run services metrics list --service=$SERVICE_NAME --region=$REGION

# Check 3: Review connection pool settings
# Increase pool size if needed in DATABASE_URL

# Fix: Optimize database connections
gcloud run services update $SERVICE_NAME \
    --set-env-vars="DB_POOL_SIZE=30,DB_MAX_OVERFLOW=50" \
    --region=$REGION
```

---

## 🔄 Post-Deployment Activities

### **Immediate (First 24 hours)**
1. **Monitor Service Health**: Watch metrics and logs for any issues
2. **Performance Baseline**: Establish performance benchmarks
3. **User Acceptance**: Test all major user workflows
4. **Documentation Update**: Update team documentation with new URLs

### **Short-term (First week)**
1. **Load Testing**: Test with realistic user load patterns
2. **Backup Verification**: Verify automated backups are working
3. **Security Review**: Complete security validation checklist
4. **Cost Monitoring**: Set up cost alerts and optimization

### **Medium-term (First month)**
1. **User Migration**: Plan and execute user migration if needed
2. **Performance Optimization**: Fine-tune based on usage patterns
3. **Capacity Planning**: Plan for growth and scaling
4. **Original Service Sunset**: Plan decommissioning of ephemeral service

---

## 📋 Success Metrics

### **Technical Metrics**
- **Uptime**: ≥99.9% service availability
- **Response Time**: ≤100ms average API response time
- **Database Performance**: ≤50ms average query time
- **Error Rate**: <0.1% error rate across all endpoints

### **Business Metrics**
- **Data Persistence**: 0 incidents of data loss
- **User Experience**: All user workflows functional
- **Resume Generation**: PDF generation success rate ≥99%
- **Scalability**: Support for 100+ concurrent users

### **Operational Metrics**
- **Deployment Success**: Successful deployment without rollback
- **Monitoring Coverage**: All critical metrics monitored
- **Alert Response**: <5 minute response to critical alerts
- **Cost Efficiency**: Database costs within $20/month budget

---

**Deployment Status**: ✅ **READY FOR EXECUTION**  
**Estimated Duration**: 3-4 hours total deployment time  
**Next Steps**: Execute deployment following this guide step-by-step  
**Support**: Reference troubleshooting section for common issues