#!/bin/bash
#
# Script: 02_setup_psc.sh
# Description: Creates the Private Service Connect (PSC) interface using network attachments.
#
# Instructions:
#   1. Ensure you have run `01_setup_database.sh` successfully.
#   2. Run this script from your terminal: ./02_setup_psc.sh
#

# --- Load Environment Variables ---
source ./variables.sh
if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "your-gcp-project-id" ]]; then
    echo "❌ Error: PROJECT_ID is not set. Please edit variables.sh"
    exit 1
fi

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Step 1: Setting active project to $PROJECT_ID ---"
gcloud config set project $PROJECT_ID

echo "--- Step 2: Enabling required APIs ---"
gcloud services enable \
  compute.googleapis.com \
  aiplatform.googleapis.com

echo "--- Step 3: Creating Network Attachment for PSC Interface ---"

# Create network attachment name based on our demo prefix
NETWORK_ATTACHMENT_NAME="${DEMO_PREFIX}-network-attachment"

# Check if network attachment already exists
if ! gcloud compute network-attachments describe "$NETWORK_ATTACHMENT_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating network attachment for Agent Engine PSC interface..."
    gcloud compute network-attachments create "$NETWORK_ATTACHMENT_NAME" \
        --region="$REGION" \
        --connection-preference=ACCEPT_MANUAL \
        --subnets="$SUBNET_NAME" \
        --project="$PROJECT_ID"
    
    echo "✅ Network attachment '$NETWORK_ATTACHMENT_NAME' created successfully."
else
    echo "Network attachment '$NETWORK_ATTACHMENT_NAME' already exists."
fi

echo "--- Step 4: Granting permissions to Vertex AI service agent (if needed) ---"
# Get project number for the service agent
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
VERTEX_AI_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-vertex-ai.iam.gserviceaccount.com"

# Check if the service account exists before granting permissions
if gcloud iam service-accounts describe "${VERTEX_AI_SERVICE_AGENT}" --project="$PROJECT_ID" &>/dev/null; then
    echo "Granting compute.networkAdmin role to Vertex AI service agent..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${VERTEX_AI_SERVICE_AGENT}" \
        --role="roles/compute.networkAdmin" \
        --condition=None \
        --quiet
else
    echo "Note: Vertex AI service agent will be created automatically when you first use Vertex AI services."
    echo "The network permissions will be granted automatically at that time."
fi

echo "✅ PSC Interface setup complete using network attachment approach."
echo "Network attachment: $NETWORK_ATTACHMENT_NAME"
echo "Region: $REGION" 
echo "Subnet: $SUBNET_NAME"
echo "Agent Engine can now securely connect to your VPC through the PSC interface."
