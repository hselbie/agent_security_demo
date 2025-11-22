#!/bin/bash
#
# Script: 01_setup_database.sh
# Description: Sets up the VPC network and a private Cloud SQL instance.
#
# Instructions:
#   1. Make sure you have filled out the `variables.sh` file.
#   2. Run this script from your terminal: ./01_setup_database.sh
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

echo "--- Step 2: Enabling required GCP APIs ---"
gcloud services enable \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  iap.googleapis.com \
  sqladmin.googleapis.com

echo "--- Step 3: Creating VPC Network and Subnet (if they don't exist) ---"
if ! gcloud compute networks describe "$VPC_NETWORK" &>/dev/null; then
  gcloud compute networks create "$VPC_NETWORK" --subnet-mode=custom --bgp-routing-mode=regional
else
  echo "VPC Network '$VPC_NETWORK' already exists."
fi

if ! gcloud compute networks subnets describe "$SUBNET_NAME" --region="$REGION" &>/dev/null; then
  gcloud compute networks subnets create "$SUBNET_NAME" \
    --network="$VPC_NETWORK" \
    --range=10.0.1.0/24 \
    --region="$REGION"
else
  echo "Subnet '$SUBNET_NAME' already exists."
fi

echo "--- Step 3a: Creating IAP SSH Firewall Rule (if it doesn't exist) ---"
if ! gcloud compute firewall-rules describe allow-ssh-iap --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating firewall rule to allow SSH via IAP..."
    gcloud compute firewall-rules create allow-ssh-iap \
        --network="$VPC_NETWORK" \
        --allow=tcp:22 \
        --source-ranges="35.235.240.0/20" \
        --description="Allow SSH connections from Google Cloud's Identity-Aware Proxy" \
        --project="$PROJECT_ID"
else
    echo "Firewall rule 'allow-ssh-iap' already exists."
fi

echo "--- Step 4: Configuring Private Service Access for Cloud SQL (if needed) ---"
PEERING_RANGE_NAME="google-managed-services-$VPC_NETWORK"
if ! gcloud compute addresses describe "$PEERING_RANGE_NAME" --global &>/dev/null; then
  gcloud compute addresses create "$PEERING_RANGE_NAME" \
      --global \
      --purpose=VPC_PEERING \
      --addresses=10.1.0.0 \
      --prefix-length=16 \
      --network="$VPC_NETWORK"
else
    echo "Allocated IP range '$PEERING_RANGE_NAME' already exists."
fi

if ! gcloud services vpc-peerings list --network="$VPC_NETWORK" | grep -q servicenetworking-googleapis-com; then
  gcloud services vpc-peerings connect \
      --service=servicenetworking.googleapis.com \
      --ranges="$PEERING_RANGE_NAME" \
      --network="$VPC_NETWORK"
else
    echo "VPC peering for servicenetworking.googleapis.com already exists."
fi


echo "--- Step 5: Creating Private Cloud SQL Instance (if it doesn't exist) ---"
if ! gcloud sql instances describe "$DB_INSTANCE_NAME" &>/dev/null; then
  gcloud sql instances create "$DB_INSTANCE_NAME" \
    --database-version=POSTGRES_13 \
    --region="$REGION" \
    --network="projects/$PROJECT_ID/global/networks/$VPC_NETWORK" \
    --no-assign-ip \
    --tier=db-g1-small \
    --project="$PROJECT_ID"
else
    echo "Cloud SQL Instance '$DB_INSTANCE_NAME' already exists."
fi

echo "--- Waiting for instance to be runnable ---"
while [[ "$(gcloud sql instances describe "$DB_INSTANCE_NAME" --format='value(state)')" != "RUNNABLE" ]]; do
  echo -n "."
  sleep 10
done
echo "Instance is RUNNABLE."


echo "--- Step 6: Setting Database Password ---"
# This command will succeed even if the password is the same.
gcloud sql users set-password postgres \
  --instance="$DB_INSTANCE_NAME" \
  --password="$DB_PASSWORD"

echo "--- Step 7: Creating and Populating Database Table via a persistent VM ---"

# ==============================================================================
# SECURITY WARNING:
# In a production environment, it is strongly recommended to use ephemeral
# resources for tasks like this. Leaving a VM running permanently inside your
# VPC increases the potential attack surface.
#
# This VM is being left running FOR DEMO PURPOSES ONLY, per user request,
# to potentially facilitate later steps. Remember to manually delete this VM
# ('db-access-vm') after you have completed the demo.
# ==============================================================================

DB_ACCESS_VM_NAME="db-access-vm"
ZONE="${REGION}-a" # Derive a zone from the region

# First, get the private IP address of the database instance with a retry loop.
echo "Fetching private IP of the database instance..."
DB_PRIVATE_IP=""
for i in {1..5}; do
    DB_PRIVATE_IP=$(gcloud sql instances describe "$DB_INSTANCE_NAME" --project="$PROJECT_ID" --format='value(ipAddresses.ipAddress.extract(type=PRIVATE))' 2>/dev/null)
    if [[ -n "$DB_PRIVATE_IP" ]]; then
        break
    fi
    echo "Attempt $i: Private IP not available yet, retrying in 10 seconds..."
    sleep 10
done

if [[ -z "$DB_PRIVATE_IP" ]]; then
    echo "❌ Error: Could not retrieve the private IP for the database instance after several attempts."
    exit 1
fi
echo "Database private IP is: $DB_PRIVATE_IP"

echo "--- Creating persistent VM '$DB_ACCESS_VM_NAME' to access the private database ---"
if ! gcloud compute instances describe "$DB_ACCESS_VM_NAME" --zone="$ZONE" --project="$PROJECT_ID" &>/dev/null; then
  gcloud compute instances create "$DB_ACCESS_VM_NAME" \
      --project="$PROJECT_ID" \
      --zone="$ZONE" \
      --machine-type=e2-micro \
      --network="$VPC_NETWORK" \
      --subnet="$SUBNET_NAME" \
      --image-family=debian-11 \
      --image-project=debian-cloud \
      --scopes=https://www.googleapis.com/auth/sqlservice.admin \
      --quiet
else
    echo "VM '$DB_ACCESS_VM_NAME' already exists. Skipping creation."
fi

# Poll until SSH is ready to be more robust than a fixed sleep.
echo "Waiting for VM to be ready for SSH..."
until gcloud compute ssh "$DB_ACCESS_VM_NAME" --zone="$ZONE" --project="$PROJECT_ID" --quiet --command="echo VM is ready" &>/dev/null; do
    echo -n "."
    sleep 5
done
echo "VM is ready."

echo "--- Connecting to VM to run robust SQL setup ---"
# This command is hardened to deal with apt lock issues on new VMs.
ROBUST_SQL_SETUP_COMMAND=$(cat <<'END_COMMAND'
echo "Waiting for and stopping any automatic updates that may hold a lock..."
sudo killall apt apt-get || true
sleep 2 # Give processes time to terminate
sudo rm /var/lib/dpkg/lock-frontend || true
sudo rm /var/lib/dpkg/lock || true
sudo dpkg --configure -a

echo "Forcefully removing man-db to prevent installation hangs..."
sudo dpkg --remove --force-remove-reinstreq man-db

echo "Fixing any broken dependencies..."
sudo apt-get -f install -y --no-install-recommends > /dev/null

echo "Installing PostgreSQL client..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get -y update > /dev/null
sudo apt-get -y install --no-install-recommends postgresql-client > /dev/null

echo "Connecting to database to create and populate table..."
export PGPASSWORD='$DB_PASSWORD'
psql --host '$DB_PRIVATE_IP' --username postgres --dbname postgres --command "CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, name VARCHAR(50), role VARCHAR(50)); INSERT INTO employees (name, role) VALUES ('Alice', 'Engineer'), ('Bob', 'Manager') ON CONFLICT DO NOTHING; SELECT * FROM employees;"
END_COMMAND
)

# Inject the shell variables into the command string
# Using eval is safe here because the variables are controlled within our script.
eval "FORMATTED_COMMAND=\"$ROBUST_SQL_SETUP_COMMAND\""

# Execute the robust command via SSH
gcloud compute ssh "$DB_ACCESS_VM_NAME" --zone="$ZONE" --project="$PROJECT_ID" --quiet --command="$FORMATTED_COMMAND"

echo "✅ Database setup complete. The persistent VM '$DB_ACCESS_VM_NAME' is running."

