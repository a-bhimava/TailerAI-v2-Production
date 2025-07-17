# Data Persistence Implementation Guide for TailerAI v2.0

**Document Status:** Active | **Version:** 1.0 | **Date:** July 17, 2025  
**Author:** TailerAI Development Team  
**Purpose:** Step-by-step implementation guide for migrating from SQLite to Cloud SQL PostgreSQL  
**Prerequisites:** PRD_DATA_PERSISTENCE_ENGINE.md and CLOUD_SQL_INTEGRATION_STRATEGY.md reviewed

---

## 📋 Implementation Overview

### **Implementation Strategy**
This guide implements a **safe parallel deployment** approach, creating a new Google Cloud project with Cloud SQL PostgreSQL while keeping the existing production service completely untouched.

### **Implementation Timeline**
- **Total Duration**: 3-4 hours
- **Parallel Operation**: 2-4 weeks for thorough testing
- **Migration Window**: 1-2 hours for final switchover

---

## 🚀 Phase 1: New Google Cloud Project Setup (45 minutes)

### **Step 1.1: Create New Google Cloud Project**

#### **Manual Steps (Required)**
1. **Navigate to Google Cloud Console**: https://console.cloud.google.com/
2. **Create New Project**:
   ```
   Project Name: TailerAI Persistent v2
   Project ID: tailerai-persistent-v2
   Organization: [Your Organization]
   ```
3. **Enable Billing**: Link to your existing billing account
4. **Set as Current Project**: Select the new project in the console

#### **Automated Steps (Run in Terminal)**
```bash
# Set project variables
export NEW_PROJECT_ID="tailerai-persistent-v2"
export REGION="us-central1"
export ZONE="us-central1-a"
export SERVICE_NAME="tailerai-v2"

# Set current project
gcloud config set project $NEW_PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
gcloud config set run/region $REGION

# Verify configuration
gcloud config list
```

### **Step 1.2: Enable Required APIs**
```bash
# Enable all required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

### **Step 1.3: Create Service Account**
```bash
# Create service account for Cloud Run
gcloud iam service-accounts create tailerai-v2-sa \
    --description="TailerAI v2.0 Service Account for Persistent Storage" \
    --display-name="TailerAI v2.0 Persistent"

# Get service account email
export SERVICE_ACCOUNT="tailerai-v2-sa@$NEW_PROJECT_ID.iam.gserviceaccount.com"
echo "Service Account: $SERVICE_ACCOUNT"

# Grant required permissions
gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/logging.logWriter"
```

---

## 🗄️ Phase 2: Cloud SQL PostgreSQL Setup (60 minutes)

### **Step 2.1: Create Cloud SQL Instance**
```bash
# Set database variables
export DB_INSTANCE_NAME="tailerai-db"
export DB_NAME="tailerai_production"
export DB_USER="tailerai_user"

# Generate secure database password (save this!)
export DB_PASSWORD=$(openssl rand -base64 32)
echo "Database Password (SAVE THIS): $DB_PASSWORD"

# Create Cloud SQL instance
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --maintenance-release-channel=production \
    --deletion-protection
```

### **Step 2.2: Configure Database**
```bash
# Create database
gcloud sql databases create $DB_NAME \
    --instance=$DB_INSTANCE_NAME

# Create database user
gcloud sql users create $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_PASSWORD

# Verify setup
gcloud sql instances describe $DB_INSTANCE_NAME
gcloud sql databases list --instance=$DB_INSTANCE_NAME
gcloud sql users list --instance=$DB_INSTANCE_NAME
```

### **Step 2.3: Configure Cloud SQL IAM Authentication**
```bash
# Enable IAM authentication for the instance
gcloud sql instances patch $DB_INSTANCE_NAME \
    --database-flags=cloudsql.iam_authentication=on

# Grant Cloud SQL IAM authentication to service account
gcloud sql users create $SERVICE_ACCOUNT \
    --instance=$DB_INSTANCE_NAME \
    --type=cloud_iam_service_account
```

---

## 🔐 Phase 3: Secret Management (30 minutes)

### **Step 3.1: Create Secrets in Secret Manager**

**Get existing secrets from original project (if needed):**
```bash
# Switch to original project to get secrets
export ORIGINAL_PROJECT_ID="tailerai-34742245611"
gcloud config set project $ORIGINAL_PROJECT_ID

# Export existing secrets
export GEMINI_API_KEY=$(gcloud secrets versions access latest --secret="tailerai-gemini-api-key")
export SECRET_KEY=$(gcloud secrets versions access latest --secret="tailerai-secret-key")
export JWT_SECRET_KEY=$(gcloud secrets versions access latest --secret="tailerai-jwt-secret")

# Switch back to new project
gcloud config set project $NEW_PROJECT_ID
```

**Create secrets in new project:**
```bash
# Create database password secret
echo -n "$DB_PASSWORD" | gcloud secrets create tailerai-db-password \
    --data-file=-

# Create application secrets (using values from original project)
echo -n "$GEMINI_API_KEY" | gcloud secrets create tailerai-gemini-api-key \
    --data-file=-

echo -n "$SECRET_KEY" | gcloud secrets create tailerai-secret-key \
    --data-file=-

echo -n "$JWT_SECRET_KEY" | gcloud secrets create tailerai-jwt-secret \
    --data-file=-

# Verify secrets created
gcloud secrets list
```

### **Step 3.2: Grant Secret Access to Service Account**
```bash
# Grant access to all secrets
for secret in tailerai-db-password tailerai-gemini-api-key tailerai-secret-key tailerai-jwt-secret; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor"
done
```

---

## 🔧 Phase 4: Application Configuration (30 minutes)

### **Step 4.1: Update Application Dependencies**

**Update `requirements.txt`:**
```bash
# Navigate to project directory
cd /Users/aditya/Documents/Tailor/TailerAI-v2-Production

# Add PostgreSQL driver to requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt

# Verify addition
tail -5 requirements.txt
```

### **Step 4.2: Update Database Configuration**

**Update `app/config/settings.py`:**
```python
# Add PostgreSQL-specific configuration
class Settings(BaseSettings):
    # ... existing configuration ...
    
    # Enhanced database settings for Cloud SQL
    database_url: str = Field(
        default="sqlite:///./data/database/tailer_v2.db",
        env="DATABASE_URL"
    )
    
    # Cloud SQL specific settings
    cloud_sql_instance: str = Field(default="", env="CLOUD_SQL_INSTANCE")
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    db_pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
```

### **Step 4.3: Create Environment Configuration**

**Create `deploy/cloud-run-persistent.yaml`:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: tailerai-v2
  namespace: 'tailerai-persistent-v2'
  labels:
    cloud.googleapis.com/location: us-central1
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        # Cloud SQL connection
        run.googleapis.com/cloudsql-instances: 'tailerai-persistent-v2:us-central1:tailerai-db'
        
        # Auto-scaling configuration
        autoscaling.knative.dev/maxScale: '10'
        autoscaling.knative.dev/minScale: '0'
        
        # Performance settings
        run.googleapis.com/memory: 2Gi
        run.googleapis.com/cpu: '2'
        run.googleapis.com/timeout: '300s'
        
    spec:
      containerConcurrency: 100
      timeoutSeconds: 300
      containers:
      - image: gcr.io/tailerai-persistent-v2/tailerai-v2:latest
        name: tailerai-v2
        ports:
        - name: http1
          containerPort: 8080
        
        # Environment variables
        env:
        - name: ENVIRONMENT
          value: production
        - name: DEBUG
          value: 'False'
        - name: HOST
          value: '0.0.0.0'
        - name: PORT
          value: '8080'
        - name: LOG_LEVEL
          value: 'INFO'
        - name: LATEX_ENGINE
          value: pdflatex
        - name: LATEX_ENGINE_PATH
          value: /usr/bin/pdflatex
        
        # Database configuration
        - name: DATABASE_URL
          value: 'postgresql://tailerai_user@tailerai-persistent-v2:us-central1:tailerai-db/tailerai_production'
        - name: CLOUD_SQL_INSTANCE
          value: 'tailerai-persistent-v2:us-central1:tailerai-db'
        - name: DB_POOL_SIZE
          value: '20'
        - name: DB_MAX_OVERFLOW
          value: '30'
        - name: DB_POOL_RECYCLE
          value: '3600'
        
        # Secrets from Secret Manager
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: tailerai-gemini-api-key
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: tailerai-secret-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: tailerai-jwt-secret
        
        # Resource limits
        resources:
          limits:
            cpu: '2'
            memory: 2Gi
          requests:
            cpu: '1'
            memory: 1Gi
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
      
      # Service account
      serviceAccountName: 'tailerai-v2-sa@tailerai-persistent-v2.iam.gserviceaccount.com'
      
  traffic:
  - percent: 100
    latestRevision: true
```

---

## 🚀 Phase 5: Container Build and Deployment (45 minutes)

### **Step 5.1: Build Container for New Project**
```bash
# Navigate to project directory
cd /Users/aditya/Documents/Tailor/TailerAI-v2-Production

# Build container for new project
docker build --platform linux/amd64 -t gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest .

# Configure Docker for new project
gcloud auth configure-docker

# Push container to new project registry
docker push gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest

# Verify image pushed
gcloud container images list --repository=gcr.io/$NEW_PROJECT_ID
```

### **Step 5.2: Deploy to Cloud Run**
```bash
# Deploy using YAML configuration
gcloud run services replace deploy/cloud-run-persistent.yaml \
    --region=$REGION

# Alternative: Deploy using command line
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300s \
    --concurrency 100 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8080 \
    --service-account=$SERVICE_ACCOUNT \
    --add-cloudsql-instances $NEW_PROJECT_ID:$REGION:$DB_INSTANCE_NAME \
    --set-env-vars="ENVIRONMENT=production,DEBUG=False,DATABASE_URL=postgresql://tailerai_user@$NEW_PROJECT_ID:$REGION:$DB_INSTANCE_NAME/tailerai_production" \
    --set-secrets="GEMINI_API_KEY=tailerai-gemini-api-key:latest,SECRET_KEY=tailerai-secret-key:latest,JWT_SECRET_KEY=tailerai-jwt-secret:latest"

# Get service URL
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
```

---

## 🧪 Phase 6: Testing and Validation (30 minutes)

### **Step 6.1: Health Check Validation**
```bash
# Test health endpoint
curl -f $SERVICE_URL/health
# Expected response: {"status": "healthy", "timestamp": "..."}

# Test with verbose output
curl -v $SERVICE_URL/health
```

### **Step 6.2: Database Connectivity Test**
```bash
# View application logs to verify database connection
gcloud run services logs tail $SERVICE_NAME --region=$REGION

# Look for successful database connection messages
```

### **Step 6.3: Full Application Testing**
```bash
# Test main application endpoint
curl $SERVICE_URL/

# Test API documentation
curl $SERVICE_URL/docs

# Test authentication endpoints
curl -X POST $SERVICE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","username":"testuser"}'
```

### **Step 6.4: Data Persistence Validation**

**Test data persistence across container restarts:**
```bash
# Create test user data via API
# (Use actual frontend or API calls to create test data)

# Force container restart by deploying same image
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$NEW_PROJECT_ID/tailerai-v2:latest \
    --region $REGION

# Verify data persists after restart
# (Check that test data is still accessible)
```

---

## 🔍 Phase 7: Monitoring Setup (30 minutes)

### **Step 7.1: Enable Cloud SQL Monitoring**
```bash
# Create monitoring dashboard for Cloud SQL
gcloud monitoring dashboards create --config-from-file=- <<EOF
{
  "displayName": "TailerAI v2.0 - Database Monitoring",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Database CPU Utilization",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"$NEW_PROJECT_ID:$DB_INSTANCE_NAME\"",
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
```

### **Step 7.2: Create Alerting Policies**
```bash
# Create alert policy for database connectivity
gcloud alpha monitoring policies create --policy-from-file=- <<EOF
{
  "displayName": "TailerAI Database Connectivity Alert",
  "conditions": [{
    "displayName": "Database Connection Failures",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\"",
      "comparison": "COMPARISON_GREATER_THAN",
      "thresholdValue": 5,
      "duration": "300s"
    }
  }],
  "enabled": true
}
EOF
```

---

## ✅ Phase 8: Production Readiness Checklist

### **Step 8.1: Verify All Components**
- [ ] **Cloud SQL Instance**: Running and accessible
- [ ] **Database**: Created with proper user permissions
- [ ] **Cloud Run Service**: Deployed and responding to health checks
- [ ] **Service Account**: Configured with correct permissions
- [ ] **Secrets**: All secrets accessible from application
- [ ] **Monitoring**: Basic monitoring and alerting configured

### **Step 8.2: Performance Validation**
- [ ] **Response Times**: API responses ≤ previous SQLite performance
- [ ] **Database Connections**: Connection pool working correctly
- [ ] **Memory Usage**: Application memory usage within limits
- [ ] **Error Rates**: No increase in error rates

### **Step 8.3: Data Persistence Validation**
- [ ] **Container Restarts**: Data persists across restarts
- [ ] **Deployments**: Data persists across deployments
- [ ] **Resume Generation**: PDF generation works with persistent storage
- [ ] **User Sessions**: User authentication and sessions work correctly

---

## 🔄 Next Steps

### **Immediate (Post-Implementation)**
1. **Performance Monitoring**: Monitor service for 24-48 hours
2. **Load Testing**: Test with realistic user load
3. **Documentation Update**: Update main documentation with new URLs
4. **Team Communication**: Notify team of successful implementation

### **Short-term (1-2 weeks)**
1. **User Migration Planning**: Plan migration from original service if needed
2. **Domain Configuration**: Update DNS if switching domains
3. **Original Service Sunset**: Plan decommissioning of ephemeral service
4. **Performance Optimization**: Fine-tune based on usage patterns

### **Long-term (1-3 months)**
1. **Capacity Planning**: Monitor and plan for growth
2. **Backup Testing**: Regular backup and recovery testing
3. **Security Review**: Comprehensive security audit
4. **Cost Optimization**: Optimize resources based on usage patterns

---

## 🚨 Troubleshooting

### **Common Issues and Solutions**

#### **Database Connection Issues**
```bash
# Check Cloud SQL instance status
gcloud sql instances describe $DB_INSTANCE_NAME

# Test connectivity from Cloud Shell
gcloud sql connect $DB_INSTANCE_NAME --user=$DB_USER --database=$DB_NAME

# Check Cloud Run logs for connection errors
gcloud run services logs tail $SERVICE_NAME --region=$REGION
```

#### **Authentication Issues**
```bash
# Verify service account permissions
gcloud projects get-iam-policy $NEW_PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT"

# Check secret access
gcloud secrets versions access latest --secret="tailerai-gemini-api-key"
```

#### **Performance Issues**
```bash
# Monitor database performance
gcloud sql operations list --instance=$DB_INSTANCE_NAME

# Check Cloud Run metrics
gcloud run services metrics list \
    --service=$SERVICE_NAME \
    --region=$REGION
```

### **Emergency Rollback Procedure**
If critical issues arise:
1. **Immediate**: Direct traffic back to original service
2. **Investigation**: Analyze logs and metrics to identify issues
3. **Resolution**: Fix issues and redeploy
4. **Verification**: Thorough testing before switching back

---

**Implementation Status**: ✅ **READY FOR EXECUTION**  
**Estimated Duration**: 3-4 hours  
**Dependencies**: Google Cloud project, billing account, domain access  
**Next Document**: CLOUD_SQL_DEPLOYMENT_GUIDE.md for detailed deployment procedures