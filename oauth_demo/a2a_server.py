import os
import logging
from typing import Dict, List, Any

from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from dotenv import load_dotenv
import uvicorn
import agent # Assuming agent.py is in the same directory

from agent_executor import OAuthAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host: str = "0.0.0.0"
try:
    port: int = int(os.environ.get("PORT", "10003"))
except ValueError:
    logger.error("Invalid PORT environment variable. Using default port 10003.")
    port = 10003
PUBLIC_URL: str = os.environ.get("PUBLIC_URL", f"http://{host}:{port}")

# Retrieve BigQuery scopes from environment
BIGQUERY_SCOPES_STR: str = os.environ.get("BIGQUERY_SCOPES", "https://www.googleapis.com/auth/bigquery")
BIGQUERY_SCOPES_LIST: List[str] = BIGQUERY_SCOPES_STR.split() if BIGQUERY_SCOPES_STR else ["https://www.googleapis.com/auth/bigquery"]

runner: Runner = Runner(
    agent=agent.root_agent,
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService(),
    memory_service=InMemoryMemoryService(),
    app_name="oauth_demo",
)

agent_card: AgentCard = AgentCard(
    agent_id="oauth_agent",
    name="OAuth Agent",
    description="An agent that can access BigQuery using OAuth.",
    capabilities=AgentCapabilities(),
    skills=[AgentSkill(name="query", id="query", description="Perform a query", tags=[])],
    public_url=PUBLIC_URL,
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    url=PUBLIC_URL,
    version="1.0",
    securitySchemes={
        "google_oauth": {
            "type": "openIdConnect",
            "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration",
            "description": "Google OAuth 2.0"
        }
    },
    security=[
        {
            "google_oauth": BIGQUERY_SCOPES_LIST # Use scopes from environment
        }
    ]
)

http_handler = DefaultRequestHandler(
    agent_executor=OAuthAgentExecutor(runner, agent_card),
    task_store=InMemoryTaskStore(),
)

app: A2ARESTFastAPIApplication = A2ARESTFastAPIApplication(
    agent_card=agent_card,
    http_handler=http_handler,
).build()


if __name__ == "__main__":
    logger.info("Available routes:")
    for route in app.routes:
        logger.info(f"  {route.path}")
    uvicorn.run(app, host=host, port=port)