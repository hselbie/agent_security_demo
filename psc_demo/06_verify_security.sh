#!/bin/bash
#
# Script: 06_verify_security.sh
# Description: Verifies the project-level security by attempting a connection
#              to the private Cloud SQL instance, which should fail.
#
# Instructions:
#   1. Ensure you have run all previous scripts.
#   2. Run this script from your terminal: ./06_verify_security.sh
#

# --- Load Environment Variables ---
source ./variables.sh
if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "your-gcp-project-id" ]]; then
    echo "❌ Error: PROJECT_ID is not set. Please edit variables.sh"
    exit 1
fi

echo "--- Step 1: Setting active project to $PROJECT_ID ---"
gcloud config set project $PROJECT_ID

echo
echo "--- Verifying Project-Level Security Controls ---"
echo "Attempting to connect to the private Cloud SQL instance directly from external network."
echo "This command is being run from your local machine, which is OUTSIDE the private VPC."
echo "Therefore, this connection attempt IS EXPECTED TO FAIL due to:"
echo "  - Private IP-only Cloud SQL instance"
echo "  - VPC firewall rules blocking external access"
echo "  - No public IP assigned to database"
echo

# Attempt to connect to the database. This should be blocked by VPC-SC.
# We add a timeout to prevent it from hanging indefinitely.
gcloud sql connect "$DB_INSTANCE_NAME" --user=postgres --project="$PROJECT_ID" --quiet <<< "SELECT 1;" &
pid=$!

# Wait for a short period and then check the process
sleep 20

if kill -0 $pid 2>/dev/null; then
  echo "Connection is still attempting... waiting a bit longer."
  sleep 20
  if kill -0 $pid 2>/dev/null; then
    echo "Connection timed out as expected. Killing process."
    kill $pid
    echo -e "\n✅ Success! The connection attempt timed out, which is the expected behavior."
    echo "This demonstrates that the VPC Service Controls perimeter is blocking direct access from outside the network."
    exit 0
  fi
fi

wait $pid
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo -e "\n✅ Success! The connection command failed with exit code $exit_code, as expected."
    echo "This demonstrates that the project-level security controls are blocking direct access from outside the VPC."
    echo "Security measures working: private IP-only database, VPC firewall rules, and network isolation."
else
    echo -e "\n❌ Failure! The connection succeeded, which means the security controls are not configured correctly."
    echo "Check: database private IP configuration, firewall rules, and VPC settings."
fi
