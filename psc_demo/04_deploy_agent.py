#
# Script: 04_deploy_agent.py
# Description: Deploys the ADK agent to Agent Engine.
#
# Instructions:
#   1. Make sure you have run the previous setup scripts.
#   2. Ensure you have installed the required packages: pip install -r requirements.txt
#   3. Run this script from your terminal: python3 04_deploy_agent.py
#
import os
import vertexai
from vertexai import agent_engines
from agent import root_agent # Import the agent defined in agent.py

# --- Load Configuration from Environment ---
# These variables are sourced from variables.sh
project_id = os.environ.get("PROJECT_ID")
region = os.environ.get("REGION")
vpc_network_name = os.environ.get("VPC_NETWORK")
network_attachment_name = os.environ.get("NETWORK_ATTACHMENT_NAME")
db_password = os.environ.get("DB_PASSWORD")
db_connection_string = os.environ.get("DB_CONNECTION_STRING")

if not all([project_id, region, vpc_network_name, db_password, db_connection_string]):
    print("❌ Error: Required environment variables are not set.")
    print("Please source the variables.sh file: `source ./variables.sh`")
    exit(1)

# Construct the full VPC network resource name
vpc_network_uri = f"projects/{project_id}/global/networks/{vpc_network_name}"

# Network attachment URI for PSC interface
if network_attachment_name:
    network_attachment_uri = f"projects/{project_id}/regions/{region}/networkAttachments/{network_attachment_name}"
    print(f"Using network attachment: {network_attachment_uri}")
else:
    network_attachment_uri = None
    print("No network attachment specified, using VPC network only.")

print(f"--- Initializing Vertex AI for project '{project_id}' in '{region}' ---")
vertexai.init(project=project_id, location=region)

print("--- Deploying Agent to Agent Engine ---")
# This is the core deployment step.
# We pass the agent object, its dependencies, and the crucial network configuration.
# The VPC network parameter enables private connectivity to Cloud SQL.
# The network attachment (created in step 2) provides PSC interface for secure communication.
# The `env_vars` are passed securely to the agent's runtime environment.
remote_agent = agent_engines.create(
    agent_engine=root_agent,
    display_name="SecureDatabaseAgentDemo",
    requirements=["google-cloud-aiplatform[adk,agent_engines]", "pg8000", "cloud-sql-python-connector"],
    network=vpc_network_uri,
    env_vars={
        "DB_PASSWORD": db_password,
        "DB_CONNECTION_STRING": db_connection_string
    }
)

agent_resource_name = remote_agent.resource_name
print(f"✅ Agent deployed successfully!")
print(f"   Resource Name: {agent_resource_name}")

# Save the resource name to a file for the next script to use
with open("agent_resource_name.txt", "w") as f:
    f.write(agent_resource_name)

print("\nAgent resource name saved to agent_resource_name.txt for testing.")
