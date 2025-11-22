#!/bin/bash
source ./variables.sh

echo "--- Creating Network Attachment for Agent Engine PSC ---"
NETWORK_ATTACHMENT_NAME="${DEMO_PREFIX}-network-attachment"

if ! gcloud compute network-attachments describe "$NETWORK_ATTACHMENT_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating network attachment..."
    gcloud compute network-attachments create "$NETWORK_ATTACHMENT_NAME" \
        --region="$REGION" \
        --connection-preference=ACCEPT_MANUAL \
        --subnets="$SUBNET_NAME" \
        --project="$PROJECT_ID"
    
    echo "✅ Network attachment '$NETWORK_ATTACHMENT_NAME' created successfully."
else
    echo "Network attachment '$NETWORK_ATTACHMENT_NAME' already exists."
fi

echo "✅ PSC setup complete using network attachment approach."
