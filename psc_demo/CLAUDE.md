# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Cloud Agent Engine security demo that showcases secure database access using Private Service Connect (PSC) and VPC Service Controls. The project demonstrates enterprise-grade security by connecting an AI agent to a private Cloud SQL database through secure network channels.

## Architecture

The demo consists of 6 sequential steps that build a secure infrastructure:
1. **Database Setup**: Creates VPC, subnet, and private Cloud SQL PostgreSQL instance
2. **PSC Interface Setup**: Creates network attachment for Private Service Connect interface
3. **VPC-SC Perimeter**: Sets up VPC Service Controls security boundary
4. **Agent Deployment**: Deploys ADK agent to Agent Engine with secure network configuration
5. **Security Testing**: Validates the secure connection works
6. **Security Verification**: Confirms the perimeter blocks unauthorized access

## Required Configuration

Before running any scripts, you MUST edit `variables.sh` to set:
- `PROJECT_ID`: Your GCP project ID
- `PROJECT_NUMBER`: Your GCP project number
- `ORGANIZATION_ID`: Your GCP organization ID (required for VPC-SC)
- `DB_PASSWORD`: Strong password for PostgreSQL database

## Common Commands

### Setup and Deployment (Run in Order)
```bash
# Set environment variables (edit variables.sh first)
source ./variables.sh

# 1. Create VPC and private Cloud SQL database
./01_setup_database.sh

# 2. Set up Private Service Connect interface with network attachment
./02_setup_psc.sh

# 3. Configure VPC Service Controls perimeter
./03_setup_vpc_sc.sh

# 4. Install Python dependencies and deploy agent
pip install -r requirements.txt
python3 04_deploy_agent.py

# 5. Test the deployed agent
python3 05_test_agent.py

# 6. Verify security perimeter (should fail - proving security)
./06_verify_security.sh
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Test agent locally (requires deployed infrastructure)
python3 05_test_agent.py
```

## Key Files

- `agent.py`: ADK agent definition with database query tool using Cloud SQL Python Connector
- `variables.sh`: Configuration file that must be edited before running demo
- `04_deploy_agent.py`: Deploys agent to Agent Engine with VPC network configuration
- `05_test_agent.py`: Tests deployed agent by querying the database
- Shell scripts (01-03, 06): Infrastructure setup using gcloud commands

## Security Architecture

The agent uses:
- **Private IP connectivity** to Cloud SQL (no public internet traffic)
- **VPC Service Controls** perimeter to prevent data exfiltration
- **Private Service Connect Interface** with network attachments for secure Agent Engine to VPC communication
- **IAM authentication** for database access via Cloud SQL Python Connector

## Updated Implementation Notes

This demo has been updated to use the modern **network attachment** approach for Private Service Connect instead of the deprecated forwarding rule to service attachment method. The key changes include:

- `02_setup_psc.sh` now creates a network attachment with `ACCEPT_MANUAL` connection preference
- Enables required APIs (`compute.googleapis.com`, `aiplatform.googleapis.com`)
- Grants necessary permissions to Vertex AI service agents when they exist
- Uses the current Vertex AI documentation-compliant PSC interface setup

## Dependencies

Core packages in `requirements.txt`:
- `google-cloud-aiplatform[adk,agent_engines]`: Agent Development Kit
- `pg8000`: PostgreSQL driver
- `cloud-sql-python-connector`: Secure Cloud SQL connectivity

## Important Notes

- Step 6 verification script is expected to fail - this proves the security perimeter is working
- Agent deployment creates `agent_resource_name.txt` file used by test script
- All scripts require proper GCP authentication (`gcloud auth login`)
- VPC Service Controls requires an Organization-level setup