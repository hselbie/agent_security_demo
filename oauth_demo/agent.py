import os
import logging
from enum import Enum
from typing import List, Optional

from google.adk.agents import Agent # Changed from llm_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.auth import AuthCredentialTypes

class EnvVarNames(str, Enum): # Renamed to avoid confusion with actual values
    """Environment variable names for the agent."""
    CLIENT_ID = "OAUTH_CLIENT_ID"
    CLIENT_SECRET = "OAUTH_CLIENT_SECRET"
    MODEL = "GEMINI_MODEL" # Assuming a generic model env var, if not, hardcode or define
    AUTH_ID = "AUTHORIZATION_ID"
    BIGQUERY_SCOPES = "BIGQUERY_SCOPES"


from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
# The following imports are kept for potential future use or if `whoami` is re-added
from google.adk.agents.callback_context import CallbackContext
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_TYPE = AuthCredentialTypes.OAUTH2

# Retrieve environment variables
OAUTH_CLIENT_ID: str = os.getenv(EnvVarNames.CLIENT_ID.value, "")
OAUTH_CLIENT_SECRET: str = os.getenv(EnvVarNames.CLIENT_SECRET.value, "")
AUTHORIZATION_ID: str = os.getenv(EnvVarNames.AUTH_ID.value, "")
BIGQUERY_SCOPES_STR: str = os.getenv(EnvVarNames.BIGQUERY_SCOPES.value, "")
GEMINI_MODEL: str = os.getenv(EnvVarNames.MODEL.value, "gemini-2.5-flash") # Default model or from env

# Basic validation
if not OAUTH_CLIENT_ID or not OAUTH_CLIENT_SECRET or not AUTHORIZATION_ID or not BIGQUERY_SCOPES_STR:
    logger.error("Missing one or more critical OAuth environment variables (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, AUTHORIZATION_ID, BIGQUERY_SCOPES). Please check your .env file.")
    # In a real app, you might raise an exception or provide mock values.
    # For demo, we'll log and proceed, but expect issues if not set.

BIGQUERY_SCOPES_LIST: List[str] = BIGQUERY_SCOPES_STR.split() if BIGQUERY_SCOPES_STR else ["https://www.googleapis.com/auth/bigquery"] # Default scope

# Define BigQuery tool config
tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

credentials_config = BigQueryCredentialsConfig(
    client_id=OAUTH_CLIENT_ID,
    client_secret=OAUTH_CLIENT_SECRET,
    scopes=BIGQUERY_SCOPES_LIST,
    authorization_id=AUTHORIZATION_ID, # Pass authorization_id to credentials_config
)

bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)

root_agent: Agent = Agent(
    model=GEMINI_MODEL,
    name="hello_agent",
    description=(
        "Agent to answer questions about BigQuery data and models and"
        " execute SQL queries."
    ),
    instruction="""\
        You are a data science agent with access to several BigQuery tools.
        Make use of those tools to answer the user's questions.
    """,
    tools=[bigquery_toolset],
)
