#!/bin/bash
#
# Description:
#   This script contains all the user-configurable variables needed to run the demo.
#   Source this file in other scripts to ensure all variables are set.
#
# Instructions:
#   1. Fill in the values for each variable below.
#   2. Save the file.
#   3. Do NOT run this script directly. It should be sourced by other scripts.
#      Example: source ./variables.sh

# --- GCP Project Configuration ---
# Your Google Cloud Project ID.
export PROJECT_ID="big-data-379417"

# Your Google Cloud Project Number.
# You can find this by running: gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
export PROJECT_NUMBER="1077649599081"

# Your GCP Organization ID (numeric).
# You can find this by running: gcloud organizations list
export ORGANIZATION_ID="716380124722"

# The region to deploy resources in.
export REGION="us-central1"

# --- Demo Resource Naming ---
# A unique prefix for the resources created in this demo to avoid naming conflicts.
export DEMO_PREFIX="agent-sec-demo"

# The name of the VPC network to be created.
export VPC_NETWORK="${DEMO_PREFIX}-vpc"

# The name of the subnet to be created.
export SUBNET_NAME="${DEMO_PREFIX}-subnet"

# The name of the Cloud SQL instance.
export DB_INSTANCE_NAME="${DEMO_PREFIX}-sql-db"

# The name of the PSC Endpoint (forwarding rule) - deprecated, kept for compatibility.
export PSC_ENDPOINT_NAME="${DEMO_PREFIX}-psc-endpoint"

# The name of the PSC Network Attachment (modern approach).
export NETWORK_ATTACHMENT_NAME="${DEMO_PREFIX}-network-attachment"

# The name of the VPC Service Controls Access Policy.
# You can find this by running: gcloud access-context-manager policies list --organization=$ORGANIZATION_ID --format="value(name)"
# If you don't have one, the setup script will create one with this title.
export ACCESS_POLICY_TITLE="MyOrgAccessPolicy"

# The name of the VPC Service Controls Perimeter.
export PERIMETER_NAME="${DEMO_PREFIX}-perimeter"

# --- Cloud SQL Database Credentials ---
# The password for the 'postgres' user on your Cloud SQL instance.
# IMPORTANT: Use a strong, unique password. Do not commit this to a public repository.
export DB_PASSWORD="your-strong-password"

# The database connection string (Project:Region:Instance).
export DB_CONNECTION_STRING="${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}"

echo "✅ Variables loaded for project: $PROJECT_ID"
