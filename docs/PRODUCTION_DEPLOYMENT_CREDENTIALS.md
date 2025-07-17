# TailerAI v2.0 Production Deployment Credentials & Configuration

**Document Status:** Active | **Version:** 1.0 | **Date:** July 17, 2025  
**Last Updated:** July 17, 2025 - Production Deployment Complete  
**Author:** TailerAI Development Team  
**Purpose:** Comprehensive record of production deployment credentials and configuration

---

## 🔐 **SECURITY NOTICE**

**⚠️ CONFIDENTIAL INFORMATION**
This document contains sensitive production credentials. Access should be restricted to authorized personnel only.

- Store this document securely
- Never commit to version control
- Rotate credentials regularly
- Follow principle of least privilege

---

## 🌐 **Production Service Information**

### **Primary Service**
- **Service Name:** `tailerai-v2`
- **Service URL:** `https://tailerai-v2-64408861474.us-central1.run.app`
- **Health Endpoint:** `https://tailerai-v2-64408861474.us-central1.run.app/health`
- **Region:** `us-central1`
- **Status:** ✅ Active and Healthy

### **Service Configuration**
- **Environment:** Production
- **Architecture:** Master Dataset
- **Database:** PostgreSQL (Cloud SQL)
- **Container Registry:** `gcr.io/tailer-466216/tailerai-v2:latest`
- **Scaling:** Auto (Min: 0, Max: 10)
- **Memory:** 2Gi
- **CPU:** 2 cores
- **Timeout:** 300 seconds

---

## 📋 **Google Cloud Project Details**

### **Project Information**
- **Project ID:** `tailer-466216`
- **Project Name:** TailerAI v2.0 Production
- **Project Number:** `64408861474`
- **Billing Account:** Linked to user account
- **Region:** `us-central1`

### **Enabled APIs**
- Cloud Run API
- Cloud SQL Admin API
- Secret Manager API
- Cloud Resource Manager API
- Container Registry API
- IAM Service Account Credentials API
- Cloud Build API
- Google Compute Engine API

---

## 🔑 **API Keys & Secrets**

### **Gemini API Key**
- **Key:** `AIzaSyA9_qFrMQu7QewVKA4bQx2B4KugiOisSGw`
- **Status:** Active
- **Usage:** AI content generation and processing
- **Storage:** Google Secret Manager (`tailerai-gemini-api-key`)
- **Limits:** 60 requests/minute, 1500 requests/day

### **Database Password**
- **Value:** `Ww2ledUgAtBSG3lXXsYsgnvic`
- **User:** `tailerai_user`
- **Database:** `tailerai_production`
- **Storage:** Google Secret Manager (`tailerai-db-password`)
- **Generated:** July 17, 2025

### **Application Secret Key**
- **Storage:** Google Secret Manager (`tailerai-secret-key`)
- **Usage:** Application encryption and session management
- **Status:** Auto-generated

### **JWT Secret Key**
- **Storage:** Google Secret Manager (`tailerai-jwt-secret`)
- **Usage:** JSON Web Token signing and verification
- **Status:** Auto-generated

---

## 🗄️ **Database Configuration**

### **Cloud SQL Instance**
- **Instance ID:** `tailerai-db`
- **Instance Name:** `tailer-466216:us-central1:tailerai-db`
- **Database Version:** PostgreSQL 13
- **Tier:** `db-f1-micro`
- **Region:** `us-central1-c`
- **Storage:** 10GB SSD with auto-resize
- **Backup:** Enabled (7 days retention)
- **Maintenance:** Sunday 4:00 AM

### **Database Connection Details**
- **Database Name:** `tailerai_production`
- **Username:** `tailerai_user`
- **Password:** `Ww2ledUgAtBSG3lXXsYsgnvic`
- **Connection String:** `postgresql://tailerai_user:Ww2ledUgAtBSG3lXXsYsgnvic@/tailerai_production?host=/cloudsql/tailer-466216:us-central1:tailerai-db`
- **SSL:** Enabled with Google-managed certificates

### **Database Users**
1. **postgres** (Built-in admin)
2. **tailerai_user** (Application user)
3. **tailerai-v2-sa@tailer-466216.iam** (Service account user)

---

## 🎛️ **Service Account Configuration**

### **Primary Service Account**
- **Name:** `tailerai-v2-sa`
- **Email:** `tailerai-v2-sa@tailer-466216.iam.gserviceaccount.com`
- **Display Name:** TailerAI v2.0 Service Account
- **Key File:** Auto-managed by Google Cloud Run

### **Assigned Roles**
- `roles/cloudsql.client` - Cloud SQL Client
- `roles/secretmanager.secretAccessor` - Secret Manager Secret Accessor
- `roles/cloudsql.instanceUser` - Cloud SQL Instance User

### **IAM Bindings**
- **Cloud Run Service:** `roles/run.invoker` → `allUsers` (Public access)
- **Secret Manager:** Service account has read access to all secrets
- **Cloud SQL:** Service account can connect to database instance

---

## 🔒 **Secret Manager Configuration**

### **Active Secrets**
1. **tailerai-gemini-api-key**
   - Value: `AIzaSyA9_qFrMQu7QewVKA4bQx2B4KugiOisSGw`
   - Version: latest
   - Created: July 17, 2025

2. **tailerai-db-password**
   - Value: `Ww2ledUgAtBSG3lXXsYsgnvic`
   - Version: latest
   - Created: July 17, 2025

3. **tailerai-secret-key**
   - Value: [Auto-generated]
   - Version: latest
   - Created: July 17, 2025

4. **tailerai-jwt-secret**
   - Value: [Auto-generated]
   - Version: latest
   - Created: July 17, 2025

5. **tailerai-database-url**
   - Value: `postgresql://tailerai_user:Ww2ledUgAtBSG3lXXsYsgnvic@/tailerai_production?host=/cloudsql/tailer-466216:us-central1:tailerai-db`
   - Version: latest
   - Created: July 17, 2025

---

## 🌍 **Environment Variables**

### **Production Environment Configuration**
```yaml
ENVIRONMENT: production
DEBUG: False
HOST: 0.0.0.0
LOG_LEVEL: INFO
LATEX_ENGINE: pdflatex
LATEX_ENGINE_PATH: /usr/bin/pdflatex

# Database Configuration
DATABASE_URL: [From Secret Manager]
CLOUD_SQL_INSTANCE: tailer-466216:us-central1:tailerai-db
DB_POOL_SIZE: 20
DB_MAX_OVERFLOW: 30
DB_POOL_RECYCLE: 3600
DB_POOL_TIMEOUT: 30
DB_POOL_PRE_PING: true

# Performance Settings
MAX_FILE_SIZE: 10485760  # 10MB
REQUEST_TIMEOUT: 300

# AI Service Configuration
ENABLE_AI_CONTENT_SELECTION: true
ENABLE_AI_ATS_OPTIMIZATION: true
ENABLE_AI_CONTENT_ENHANCEMENT: true
ENABLE_AI_PERSONALIZATION: true
GEMINI_REQUESTS_PER_MINUTE: 60
GEMINI_DAILY_LIMIT: 1500

# CORS Configuration
ALLOWED_ORIGINS: ["https://tailerai-v2-64408861474.us-central1.run.app"]

# Frontend Configuration
FRONTEND_URL: https://tailerai-v2-64408861474.us-central1.run.app
```

---

## 📊 **Monitoring & Logging**

### **Cloud Run Metrics**
- **Service:** `tailerai-v2`
- **Logs:** Available in Google Cloud Console
- **Monitoring Dashboard:** Cloud Run service overview
- **Alerts:** Not configured (future enhancement)

### **Database Monitoring**
- **Instance:** `tailerai-db`
- **Performance Insights:** Enabled
- **Query Insights:** Available
- **Backup Status:** Automated daily backups

### **Health Check Configuration**
- **Liveness Probe:** `/health` endpoint every 30s
- **Startup Probe:** Disabled (was causing deployment issues)
- **Readiness Probe:** Disabled (not supported in current project)

---

## 🔧 **Deployment Configuration**

### **Container Configuration**
- **Image:** `gcr.io/tailer-466216/tailerai-v2:latest`
- **Platform:** `linux/amd64`
- **Base Image:** Python 3.11
- **Container Port:** 8080
- **Build Date:** July 17, 2025

### **Cloud Run Service Configuration**
- **Service Name:** `tailerai-v2`
- **Namespace:** `tailer-466216`
- **Execution Environment:** Second Generation
- **Ingress:** All traffic allowed
- **Concurrency:** 100 requests per container
- **Timeout:** 300 seconds

### **Auto-scaling Configuration**
- **Minimum Instances:** 0
- **Maximum Instances:** 10
- **CPU Utilization Target:** 70%
- **Memory:** 2Gi per instance
- **CPU:** 2 cores per instance

---

## 💰 **Cost Information**

### **Estimated Monthly Costs**
- **Cloud SQL (db-f1-micro):** ~$10/month
- **Storage (10GB SSD):** ~$2/month
- **Backups:** ~$0.10/month
- **Network Egress:** ~$1-3/month
- **Cloud Run:** ~$0-5/month (usage-based)
- **Total Estimated:** ~$15-20/month

### **Usage Limits**
- **Gemini API:** 60 requests/minute, 1500/day
- **Database Connections:** 20 pool size, 30 max overflow
- **Cloud Run:** Auto-scaling based on traffic

---

## 🚀 **Deployment Commands**

### **Key Commands Used**
```bash
# Build and push container
docker build --platform linux/amd64 -t gcr.io/tailer-466216/tailerai-v2:latest .
docker push gcr.io/tailer-466216/tailerai-v2:latest

# Deploy to Cloud Run
gcloud run services replace deploy/cloud-run-persistent.yaml --region=us-central1 --project=tailer-466216

# Enable public access
gcloud run services add-iam-policy-binding tailerai-v2 --project=tailer-466216 --region=us-central1 --member="allUsers" --role="roles/run.invoker"
```

### **Configuration Files**
- **Main Config:** `deploy/cloud-run-persistent.yaml`
- **Docker Config:** `Dockerfile`
- **Dependencies:** `requirements.txt`
- **Application Config:** `app/config/settings.py`

---

## 🔍 **Verification & Testing**

### **Health Check Results**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "architecture": "master_dataset",
  "services": {
    "database": true,
    "latex_engine": true,
    "api": true
  },
  "database": {
    "status": "healthy",
    "database_type": "postgresql",
    "debug_mode": false
  },
  "debug_mode": false
}
```

### **Test Endpoints**
- **Health:** `https://tailerai-v2-64408861474.us-central1.run.app/health`
- **Root:** `https://tailerai-v2-64408861474.us-central1.run.app/`
- **API Docs:** `https://tailerai-v2-64408861474.us-central1.run.app/docs`

---

## 📚 **Documentation References**

### **Related Documents**
- **Implementation Guide:** `docs_2/implementation/DATA_PERSISTENCE_IMPLEMENTATION_GUIDE.md`
- **Architecture Design:** `docs_2/technical/persistent-storage-architecture.md`
- **Status Tracking:** `docs_2/development/DATA_PERSISTENCE_STATUS.md`
- **Deployment Guide:** `docs_2/implementation/CLOUD_SQL_DEPLOYMENT_GUIDE.md`

### **Google Cloud Console Links**
- **Project Dashboard:** `https://console.cloud.google.com/home/dashboard?project=tailer-466216`
- **Cloud Run Service:** `https://console.cloud.google.com/run/detail/us-central1/tailerai-v2?project=tailer-466216`
- **Cloud SQL Instance:** `https://console.cloud.google.com/sql/instances/tailerai-db?project=tailer-466216`
- **Secret Manager:** `https://console.cloud.google.com/security/secret-manager?project=tailer-466216`

---

## 🔄 **Maintenance & Updates**

### **Regular Maintenance Tasks**
1. **Monthly:** Review and rotate API keys
2. **Quarterly:** Update container images and dependencies
3. **Semi-Annual:** Review and optimize database performance
4. **Annual:** Comprehensive security audit

### **Emergency Contacts**
- **Technical Lead:** Access via development team
- **Database Admin:** Service account managed
- **Security Team:** Credential rotation procedures

### **Backup & Recovery**
- **Database Backups:** Automated daily backups (7-day retention)
- **Configuration Backup:** This document and config files
- **Recovery Procedure:** Documented in deployment guides

---

## 📝 **Change Log**

### **Version 1.0 - July 17, 2025**
- Initial production deployment
- PostgreSQL database setup
- Cloud Run service deployment
- Secret Manager configuration
- Service account setup
- Public access enablement

### **Future Enhancements**
- Monitoring and alerting setup
- Performance optimization
- Security hardening
- Cost optimization
- Multi-region deployment consideration

---

**Document Owner:** TailerAI Development Team  
**Next Review:** August 17, 2025  
**Classification:** Confidential - Production Credentials

---

**⚠️ IMPORTANT SECURITY REMINDER**
- Never share these credentials publicly
- Store this document in a secure location
- Rotate credentials regularly
- Follow company security policies
- Report any security incidents immediately