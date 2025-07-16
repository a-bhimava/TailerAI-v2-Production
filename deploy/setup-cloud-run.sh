#!/bin/bash

# TailerAI v2.0 - Google Cloud Run Setup Script
# This script automates the deployment setup for Google Cloud Run

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if required tools are installed
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Set up Google Cloud configuration
setup_gcloud() {
    print_header "Setting up Google Cloud Configuration"
    
    # Check if user is logged in
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        print_warning "Not logged in to Google Cloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Get project ID
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No project set. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
        exit 1
    fi
    
    print_status "Using project: $PROJECT_ID"
    
    # Set region
    REGION=${REGION:-us-central1}
    gcloud config set run/region $REGION
    print_status "Using region: $REGION"
    
    # Set service name
    SERVICE_NAME=${SERVICE_NAME:-tailerai-v2}
    print_status "Using service name: $SERVICE_NAME"
    
    # Export variables for use in other functions
    export PROJECT_ID
    export REGION
    export SERVICE_NAME
}

# Enable required APIs
enable_apis() {
    print_header "Enabling Required APIs"
    
    apis=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "containerregistry.googleapis.com"
        "secretmanager.googleapis.com"
        "monitoring.googleapis.com"
        "logging.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        print_status "Enabling $api..."
        gcloud services enable $api --quiet
    done
    
    print_status "All required APIs enabled"
}

# Create service account
create_service_account() {
    print_header "Creating Service Account"
    
    SA_NAME="tailerai-v2-sa"
    SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Check if service account already exists
    if gcloud iam service-accounts describe $SA_EMAIL --quiet 2>/dev/null; then
        print_warning "Service account $SA_EMAIL already exists"
    else
        # Create service account
        gcloud iam service-accounts create $SA_NAME \
            --description="TailerAI v2.0 Service Account" \
            --display-name="TailerAI v2.0" \
            --quiet
        
        print_status "Service account created: $SA_EMAIL"
    fi
    
    # Grant necessary permissions
    roles=(
        "roles/cloudsql.client"
        "roles/secretmanager.secretAccessor"
        "roles/logging.logWriter"
        "roles/monitoring.metricWriter"
        "roles/storage.objectViewer"
    )
    
    for role in "${roles[@]}"; do
        print_status "Granting role $role to service account..."
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SA_EMAIL" \
            --role="$role" \
            --quiet
    done
    
    print_status "Service account permissions configured"
}

# Create secrets in Secret Manager
create_secrets() {
    print_header "Creating Secrets in Secret Manager"
    
    # Function to create or update secret
    create_or_update_secret() {
        local secret_name=$1
        local secret_value=$2
        
        if gcloud secrets describe $secret_name --quiet 2>/dev/null; then
            print_warning "Secret $secret_name already exists. Updating..."
            echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
        else
            print_status "Creating secret $secret_name..."
            echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=-
        fi
    }
    
    # Generate secure random values if not provided
    if [ -z "$GEMINI_API_KEY" ]; then
        print_warning "GEMINI_API_KEY not provided. Please set it as an environment variable."
        read -p "Enter your Gemini API Key: " GEMINI_API_KEY
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(openssl rand -hex 32)
        print_status "Generated SECRET_KEY"
    fi
    
    if [ -z "$JWT_SECRET_KEY" ]; then
        JWT_SECRET_KEY=$(openssl rand -hex 32)
        print_status "Generated JWT_SECRET_KEY"
    fi
    
    # Create secrets
    create_or_update_secret "tailerai-gemini-api-key" "$GEMINI_API_KEY"
    create_or_update_secret "tailerai-secret-key" "$SECRET_KEY"
    create_or_update_secret "tailerai-jwt-secret" "$JWT_SECRET_KEY"
    
    # Optional: Google OAuth secret
    if [ -n "$GOOGLE_CLIENT_SECRET" ]; then
        create_or_update_secret "tailerai-google-client-secret" "$GOOGLE_CLIENT_SECRET"
    fi
    
    print_status "Secrets created in Secret Manager"
}

# Build and push Docker image
build_and_push_image() {
    print_header "Building and Pushing Docker Image"
    
    # Configure Docker for Container Registry
    gcloud auth configure-docker --quiet
    
    # Build image
    IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
    print_status "Building image: $IMAGE_NAME"
    
    docker build -t $IMAGE_NAME .
    
    # Push image
    print_status "Pushing image to Container Registry..."
    docker push $IMAGE_NAME
    
    print_status "Image pushed successfully"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    print_header "Deploying to Cloud Run"
    
    # Update service configuration with project ID
    sed -i.bak "s/PROJECT_ID_PLACEHOLDER/$PROJECT_ID/g" deploy/cloud-run-service.yaml
    
    # Deploy service
    print_status "Deploying service to Cloud Run..."
    gcloud run services replace deploy/cloud-run-service.yaml \
        --region=$REGION \
        --quiet
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --format="value(status.url)")
    
    print_status "Service deployed successfully!"
    print_status "Service URL: $SERVICE_URL"
    
    # Test the deployment
    print_status "Testing deployment..."
    sleep 10
    
    if curl -f "$SERVICE_URL/health" &>/dev/null; then
        print_status "Health check passed!"
    else
        print_warning "Health check failed. Please check the logs."
    fi
    
    # Restore original file
    mv deploy/cloud-run-service.yaml.bak deploy/cloud-run-service.yaml
}

# Setup Cloud Build trigger (optional)
setup_cloud_build_trigger() {
    print_header "Setting up Cloud Build Trigger (Optional)"
    
    read -p "Do you want to set up automated builds with Cloud Build? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your GitHub repository owner: " REPO_OWNER
        read -p "Enter your GitHub repository name: " REPO_NAME
        
        # Create build trigger
        gcloud builds triggers create github \
            --repo-name=$REPO_NAME \
            --repo-owner=$REPO_OWNER \
            --branch-pattern="^main$" \
            --build-config=deploy/cloudbuild.yaml \
            --description="TailerAI v2.0 automated deployment" \
            --quiet
        
        print_status "Cloud Build trigger created"
    else
        print_status "Skipping Cloud Build trigger setup"
    fi
}

# Main function
main() {
    print_header "TailerAI v2.0 - Google Cloud Run Deployment Setup"
    
    # Check if running from correct directory
    if [ ! -f "app/main.py" ]; then
        print_error "Please run this script from the TailerAI-v2-Production root directory"
        exit 1
    fi
    
    # Run setup steps
    check_prerequisites
    setup_gcloud
    enable_apis
    create_service_account
    create_secrets
    build_and_push_image
    deploy_to_cloud_run
    setup_cloud_build_trigger
    
    print_header "Deployment Complete!"
    print_status "Your TailerAI v2.0 application is now deployed to Google Cloud Run"
    print_status "Service URL: $SERVICE_URL"
    print_status "Health check: $SERVICE_URL/health"
    print_status "API docs: $SERVICE_URL/docs"
    
    print_header "Next Steps:"
    echo "1. Update your DNS to point to the Cloud Run service URL"
    echo "2. Configure custom domain in Cloud Run console"
    echo "3. Set up monitoring and alerting"
    echo "4. Configure backup strategies"
    echo "5. Review security settings"
    
    print_status "For more information, see docs/GOOGLE_CLOUD_RUN_DEPLOYMENT_GUIDE.md"
}

# Run main function
main "$@"