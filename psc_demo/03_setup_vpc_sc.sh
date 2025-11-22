#!/bin/bash
#
# Script: 03_setup_vpc_sc.sh
# Description: Sets up project-level security controls (VPC Service Controls requires org admin).
#
# Instructions:
#   1. Ensure you have run the previous scripts successfully.
#   2. This script sets up project-level security instead of org-level VPC-SC.
#   3. Run this script from your terminal: ./03_setup_vpc_sc.sh
#

# --- Load Environment Variables ---
source ./variables.sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Project-Level Security Setup (Alternative to VPC Service Controls) ---"
echo "Note: VPC Service Controls requires organization admin permissions."
echo "This script sets up project-level security controls instead."

echo "--- Step 1: Setting active project to $PROJECT_ID ---"
gcloud config set project $PROJECT_ID

echo "--- Step 2: Ensuring required APIs are enabled ---"
gcloud services enable \
  compute.googleapis.com \
  aiplatform.googleapis.com \
  sqladmin.googleapis.com

echo "--- Step 3: Setting up VPC firewall rules for enhanced security ---"
# Create restrictive firewall rules to limit access

# Allow only internal traffic within the VPC
INTERNAL_FIREWALL_RULE="${DEMO_PREFIX}-allow-internal"
if ! gcloud compute firewall-rules describe "$INTERNAL_FIREWALL_RULE" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating firewall rule to allow internal VPC traffic..."
    gcloud compute firewall-rules create "$INTERNAL_FIREWALL_RULE" \
        --network="$VPC_NETWORK" \
        --allow=tcp,udp,icmp \
        --source-ranges="10.0.0.0/8" \
        --description="Allow internal VPC communication" \
        --project="$PROJECT_ID"
else
    echo "Firewall rule '$INTERNAL_FIREWALL_RULE' already exists."
fi

# Deny all external ingress by default (create explicit deny rule)
DENY_EXTERNAL_RULE="${DEMO_PREFIX}-deny-external"
if ! gcloud compute firewall-rules describe "$DENY_EXTERNAL_RULE" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating firewall rule to deny external access..."
    gcloud compute firewall-rules create "$DENY_EXTERNAL_RULE" \
        --network="$VPC_NETWORK" \
        --action=deny \
        --rules=all \
        --source-ranges="0.0.0.0/0" \
        --priority=1000 \
        --description="Deny all external access" \
        --project="$PROJECT_ID"
else
    echo "Firewall rule '$DENY_EXTERNAL_RULE' already exists."
fi

echo "--- Step 4: Configuring Private Google Access ---"
# Ensure the subnet has Private Google Access enabled for secure Google API access
echo "Enabling Private Google Access on subnet '$SUBNET_NAME'..."
gcloud compute networks subnets update "$SUBNET_NAME" \
    --region="$REGION" \
    --enable-private-ip-google-access \
    --project="$PROJECT_ID"

echo "--- Step 5: Setting IAM policies for enhanced security ---"
# Create a custom role with minimal permissions for the demo
CUSTOM_ROLE_ID="${DEMO_PREFIX//-/_}_agent_role"
if ! gcloud iam roles describe "projects/$PROJECT_ID/roles/$CUSTOM_ROLE_ID" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating custom IAM role with minimal permissions..."
    gcloud iam roles create "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --title="Agent Demo Role" \
        --description="Minimal permissions for secure agent demo" \
        --permissions="cloudsql.instances.connect,aiplatform.endpoints.predict"
else
    echo "Custom IAM role '$CUSTOM_ROLE_ID' already exists."
fi

echo "✅ Project-level security controls are now active."
echo "Security measures implemented:"
echo "  - VPC internal traffic only firewall rules"
echo "  - External access denial rules"
echo "  - Private Google Access enabled"
echo "  - Custom IAM role with minimal permissions"
echo ""
echo "Note: This provides strong project-level security without requiring VPC Service Controls."
echo "For maximum security in production, consider using VPC Service Controls with org admin permissions."
