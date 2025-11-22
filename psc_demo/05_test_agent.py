#
# Script: 05_test_agent.py
# Description: Tests the deployed agent by sending it a query.
#
# Instructions:
#   1. Ensure the agent has been deployed successfully with `04_deploy_agent.py`.
#   2. Run this script from your terminal: python3 05_test_agent.py
#
import os
import vertexai
from vertexai import agent_engines

# --- Load Configuration ---
project_id = os.environ.get("PROJECT_ID")
region = os.environ.get("REGION")

if not all([project_id, region]):
    print("❌ Error: Required environment variables are not set.")
    print("Please source the variables.sh file: `source ./variables.sh`")
    exit(1)

try:
    with open("agent_resource_name.txt", "r") as f:
        agent_resource_name = f.read().strip()
except FileNotFoundError:
    print("❌ Error: agent_resource_name.txt not found.")
    print("Please run the deployment script (04_deploy_agent.py) first.")
    exit(1)

print(f"--- Initializing Vertex AI for project '{project_id}' in '{region}' ---")
vertexai.init(project=project_id, location=region)

print(f"--- Getting a reference to deployed agent: {agent_resource_name} ---")
remote_agent = agent_engines.get(agent_resource_name)

print("--- Creating a new session ---")
session = remote_agent.create_session(user_id="demo-user")

print("--- Sending query to the agent ---")
prompt = "List all employees"
print(f"User Prompt: \"{prompt}\"")

final_response = ""
for event in remote_agent.stream_query(
    session_id=session["id"],
    message=prompt
):
    if event.get('content') and event['content'].get('parts'):
        part_text = event['content']['parts'][0].get('text', '')
        print(f"Agent Response Chunk: {part_text}")
        final_response += part_text

print("\n--- Final Agent Response ---")
print(final_response)

# --- Verification ---
expected_result = "[('Alice', 'Engineer'), ('Bob', 'Manager')]"
if expected_result in final_response.replace("'", ""):
    print("\n✅ Success! The agent connected to the database and returned the correct data.")
else:
    print("\n❌ Failure! The agent did not return the expected data from the database.")
