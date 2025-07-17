# GitHub Actions Setup Guide for TailerAI v2.0

**Document Status:** Active | **Version:** 1.0 | **Date:** July 17, 2025  
**Last Updated:** July 17, 2025 - GitHub Actions Workflow Fixed  
**Author:** TailerAI Development Team  
**Purpose:** Setup guide for GitHub Actions CI/CD pipeline integration

---

## 🚀 **Overview**

This document provides the complete setup guide for configuring GitHub Actions to work with the TailerAI v2.0 production deployment on Google Cloud Run with PostgreSQL persistence.

## 🔧 **Recent Fixes Applied**

### **✅ Issue Resolution**
- **Problem**: GitHub Actions workflow failing with deprecated `actions/upload-artifact@v3`
- **Solution**: Updated all GitHub Actions to latest versions
- **Status**: Fixed and tested

### **✅ Updated Action Versions**
- `actions/upload-artifact`: v3 → v4
- `actions/setup-python`: v4 → v5
- `actions/cache`: v3 → v4
- `codecov/codecov-action`: v3 → v4
- `google-github-actions/setup-gcloud`: v1 → v2

### **✅ Configuration Updates**
- Updated project ID from placeholder to `tailer-466216`
- Fixed deployment file references to use persistent configuration
- Updated database configuration to use PostgreSQL
- Added Cloud SQL connection settings
- Fixed CORS and frontend URLs

---

## 🔑 **Required GitHub Secrets**

The following secrets must be configured in your GitHub repository settings:

### **1. Google Cloud Service Account Key**
- **Secret Name**: `GCP_SA_KEY`
- **Description**: Service account key for GitHub Actions authentication
- **Format**: Base64 encoded JSON service account key
- **Required**: Yes

#### **How to obtain:**
```bash
# Create a service account key for GitHub Actions
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=tailerai-v2-sa@tailer-466216.iam.gserviceaccount.com

# Base64 encode the key
cat github-actions-key.json | base64
```

### **2. Additional Secrets (Optional)**
These are already stored in Google Secret Manager and don't need GitHub secrets:
- ✅ `GEMINI_API_KEY` - Retrieved from Secret Manager
- ✅ `SECRET_KEY` - Retrieved from Secret Manager
- ✅ `JWT_SECRET_KEY` - Retrieved from Secret Manager
- ✅ `DB_PASSWORD` - Retrieved from Secret Manager

---

## 📋 **GitHub Repository Settings**

### **1. Repository Secrets Configuration**

Navigate to your GitHub repository → Settings → Secrets and variables → Actions

**Required Secrets:**
```
GCP_SA_KEY = [Base64 encoded service account key]
```

### **2. Environment Configuration**

The workflow uses the following environments:
- **Production**: Triggered on `main` branch pushes
- **Staging**: Triggered on `develop` branch pushes

### **3. Branch Protection Rules**

Recommended branch protection settings:
- **Main branch**: Require pull request reviews
- **Develop branch**: Allow merge commits
- **Status checks**: Require passing CI/CD before merge

---

## 🏗️ **Workflow Architecture**

### **Job Flow**
```
1. [Test] → Run tests and quality checks
2. [Build] → Build and push Docker image
3. [Deploy-Production] → Deploy to production (main branch)
4. [Deploy-Staging] → Deploy to staging (develop branch)
5. [Security-Scan] → Container security scanning
6. [Performance-Test] → Performance validation
7. [Cleanup] → Clean up old revisions
```

### **Trigger Conditions**
- **Push to main**: Full production deployment
- **Push to develop**: Staging deployment
- **Pull request**: Testing and validation only

---

## 🔄 **Deployment Process**

### **Production Deployment (main branch)**
1. **Test Suite**: Runs linting, tests, and security scans
2. **Build**: Creates Docker image with commit SHA tag
3. **Deploy**: Updates Cloud Run service with new image
4. **Validate**: Runs health checks and performance tests
5. **Cleanup**: Removes old revisions and images

### **Staging Deployment (develop branch)**
1. **Test Suite**: Same as production
2. **Build**: Creates Docker image
3. **Deploy**: Deploys to staging service
4. **Validate**: Basic health checks

---

## 🧪 **Testing Configuration**

### **Automated Tests**
- **Unit Tests**: pytest with coverage reporting
- **Linting**: flake8 and black formatting
- **Security**: safety and bandit scanning
- **Performance**: Apache Bench load testing

### **Health Checks**
- **Endpoint**: `/health`
- **Expected Response**: 200 OK with JSON status
- **Timeout**: 30 seconds
- **Validation**: Database connectivity and service health

---

## 📊 **Monitoring and Logging**

### **Deployment Metrics**
- **Build Time**: Docker image build duration
- **Deploy Time**: Cloud Run deployment duration
- **Health Check**: Service startup validation
- **Performance**: Response time benchmarks

### **Failure Handling**
- **Test Failures**: Continue with warnings (configurable)
- **Build Failures**: Stop deployment pipeline
- **Deploy Failures**: Rollback to previous revision
- **Health Check Failures**: Report and investigate

---

## 🛡️ **Security Considerations**

### **Secret Management**
- **GitHub Secrets**: Only for authentication keys
- **Google Secret Manager**: For application secrets
- **Service Account**: Minimal required permissions
- **Key Rotation**: Regular rotation schedule

### **Access Control**
- **Service Account**: Project-specific with limited roles
- **GitHub Actions**: Repository-specific permissions
- **Secret Access**: Read-only for deployment secrets

---

## 🚨 **Troubleshooting Guide**

### **Common Issues**

#### **1. Authentication Failures**
```
ERROR: Invalid service account key
```
**Solution**: Verify `GCP_SA_KEY` secret is properly base64 encoded

#### **2. Permission Denied**
```
ERROR: Permission denied to access Cloud Run
```
**Solution**: Ensure service account has required roles:
- `roles/run.admin`
- `roles/secretmanager.secretAccessor`
- `roles/cloudsql.client`

#### **3. Container Registry Access**
```
ERROR: Permission denied to push to gcr.io
```
**Solution**: Verify `gcloud auth configure-docker` in workflow

#### **4. Database Connection**
```
ERROR: Connection to Cloud SQL failed
```
**Solution**: Check Cloud SQL instance status and connection settings

### **Debugging Steps**

1. **Check GitHub Actions logs** for detailed error messages
2. **Verify all secrets** are properly configured
3. **Test service account permissions** locally
4. **Validate Cloud SQL connectivity** from Cloud Shell
5. **Check Secret Manager access** permissions

---

## 🔄 **Maintenance Tasks**

### **Weekly Tasks**
- Review workflow execution logs
- Monitor deployment success rates
- Check for security vulnerabilities

### **Monthly Tasks**
- Update GitHub Actions versions
- Review and rotate service account keys
- Optimize Docker build caching

### **Quarterly Tasks**
- Comprehensive security audit
- Performance optimization review
- Dependency updates and testing

---

## 📝 **Workflow Configuration Files**

### **Main Workflow**
- **File**: `.github/workflows/deploy-cloud-run.yml`
- **Purpose**: Complete CI/CD pipeline
- **Branches**: main, develop

### **Deployment Configuration**
- **File**: `deploy/cloud-run-service.yaml`
- **Purpose**: Cloud Run service configuration
- **Environment**: Production-ready with PostgreSQL

### **Docker Configuration**
- **File**: `Dockerfile`
- **Purpose**: Application containerization
- **Base**: Python 3.11 with LaTeX support

---

## 🎯 **Success Metrics**

### **Key Performance Indicators**
- **Build Success Rate**: Target >95%
- **Deploy Success Rate**: Target >98%
- **Build Time**: Target <5 minutes
- **Deploy Time**: Target <3 minutes
- **Health Check Pass Rate**: Target 100%

### **Quality Metrics**
- **Test Coverage**: Target >80%
- **Security Scan**: Zero high-severity vulnerabilities
- **Performance**: <100ms average response time
- **Uptime**: >99.9% service availability

---

## 📞 **Support and Escalation**

### **Immediate Issues**
1. Check GitHub Actions logs
2. Verify service account permissions
3. Test manual deployment process
4. Contact development team

### **Critical Failures**
1. Rollback to previous working version
2. Check Cloud SQL instance status
3. Verify Secret Manager access
4. Emergency manual deployment

---

## 🔗 **Related Documentation**

### **Internal Documentation**
- **Production Credentials**: `docs/PRODUCTION_DEPLOYMENT_CREDENTIALS.md`
- **Architecture Guide**: `docs_2/technical/persistent-storage-architecture.md`
- **Implementation Guide**: `docs_2/implementation/DATA_PERSISTENCE_IMPLEMENTATION_GUIDE.md`

### **External Resources**
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Google Cloud Run**: https://cloud.google.com/run/docs
- **Cloud SQL Documentation**: https://cloud.google.com/sql/docs

---

## 📋 **Checklist for New Setup**

### **Pre-Setup Requirements**
- [ ] Google Cloud project configured
- [ ] Service account created with proper roles
- [ ] Secret Manager secrets configured
- [ ] Cloud SQL instance running
- [ ] Cloud Run service deployed manually (for testing)

### **GitHub Configuration**
- [ ] Repository secrets added (`GCP_SA_KEY`)
- [ ] Branch protection rules configured
- [ ] Workflow file updated with project details
- [ ] Deployment configuration validated

### **Testing and Validation**
- [ ] Manual workflow trigger successful
- [ ] Health checks passing
- [ ] Database connectivity verified
- [ ] Performance benchmarks met
- [ ] Security scans clean

### **Production Readiness**
- [ ] Monitoring configured
- [ ] Alerting set up
- [ ] Documentation complete
- [ ] Team training completed
- [ ] Rollback procedures tested

---

**Document Owner:** TailerAI Development Team  
**Next Review:** August 17, 2025  
**Status:** Active - GitHub Actions Workflow Operational

---

**⚠️ IMPORTANT NOTES**
- Always test workflow changes in a feature branch first
- Monitor deployment logs for any issues
- Keep service account keys secure and rotate regularly
- Document any customizations or modifications made