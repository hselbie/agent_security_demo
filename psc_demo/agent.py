#
# File: agent.py
# Description: Defines the ADK agent and its database query tool.
#
import os
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.cloud.sql.connector import Connector
import pg8000

# --- Database Connection Tool ---
def query_database(query: str) -> str:
    """
    Queries the employees database with a given SQL query.
    Uses the Cloud SQL Python Connector to securely connect to the database
    using IAM credentials and a private IP.
    """
    print(f"Executing query: {query}")
    try:
        # These environment variables are set by the deployment script (04_deploy_agent.py)
        # and are necessary for the connector to find and authenticate to the database.
        db_connection_string = os.environ.get("DB_CONNECTION_STRING")
        db_password = os.environ.get("DB_PASSWORD")

        if not db_connection_string or not db_password:
            return "Error: Database environment variables not set."

        # The Cloud SQL Python Connector handles the secure connection logic.
        connector = Connector()
        conn = connector.connect(
            db_connection_string,
            "pg8000",
            user="postgres",
            password=db_password,
            db="postgres",
            ip_type="private"  # Ensure it connects via the private IP
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        connector.close()
        print(f"Query successful. Results: {results}")
        return str(results)
    except Exception as e:
        print(f"Error during database query: {e}")
        return f"Database query failed: {e}"

# Create a tool from the Python function.
query_tool = FunctionTool(
    func=query_database,
    description="Tool to query the employees database. Use standard SQL syntax."
)

# --- The Agent Definition ---
# This is the main ADK agent. It uses a Gemini model and is equipped with the
# database query tool we defined above.
root_agent = LlmAgent(
    model="gemini-1.5-flash",
    name="DatabaseAgent",
    instruction="""
    You are an agent that can answer questions about employees in a company.
    Use the query_database tool to query the 'employees' table.
    The table has 'id', 'name', and 'role' columns.
    When asked to list employees, use the query 'SELECT name, role FROM employees;'.
    """,
    tools=[query_tool],
)

print("✅ Agent definition loaded.")
