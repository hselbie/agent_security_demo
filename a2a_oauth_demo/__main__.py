import base64
import contextlib
import json
import logging
import os
from typing import List, Optional, Tuple, Any

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from adk_agent_executor import ADKAgentExecutor
from agents.calendar_agent import create_calendar_agent
from agents.greeter_agent import create_greeter_agent
from agents.orchestrator_agent import create_orchestrator_agent
from dotenv import load_dotenv
from google.adk.artifacts import (
    InMemoryArtifactService,  # type: ignore[import-untyped]
)
from google.adk.memory.in_memory_memory_service import (
    InMemoryMemoryService,  # type: ignore[import-untyped]
)
from google.adk.runners import Runner  # type: ignore[import-untyped]
from google.adk.sessions import (
    InMemorySessionService,  # type: ignore[import-untyped]
)
from starlette.applications import Starlette
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
    SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route


load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class InsecureJWTAuthBackend(AuthenticationBackend):
    """An example implementation of a JWT-based authentication backend."""

    async def authenticate(
        self, conn: HTTPConnection
    ) -> Optional[Tuple[AuthCredentials, BaseUser]]: # Explicit Optional and Tuple
        # For illustrative purposes only: please validate your JWTs!
        with contextlib.suppress(Exception):
            auth_header: str = conn.headers.get('Authorization', '') # Use .get with default
            if not auth_header.startswith('Bearer '):
                return None
            
            jwt: str = auth_header.split('Bearer ')[1]
            jwt_claims: str = jwt.split('.')[1]
            missing_padding: int = len(jwt_claims) % 4
            if missing_padding:
                jwt_claims += '=' * (4 - missing_padding)
            payload: str = base64.urlsafe_b64decode(jwt_claims).decode('utf-8')
            parsed_payload: Dict[str, Any] = json.loads(payload) # Explicit Dict
            return AuthCredentials([]), SimpleUser(parsed_payload['sub'])        return None


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10007)
def main(host: str, port: int):
    # Verify an API key is set.
    # Not required if using Vertex AI APIs.
    if os.getenv('GOOGLE_GENAI_USE_VERTEXAI') != 'TRUE' and not os.getenv(
        'GOOGLE_API_KEY'
    ):
        logger.error(
            'GOOGLE_API_KEY environment variable not set and '
            'GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
        )
        raise ValueError(
            'GOOGLE_API_KEY environment variable not set and '
            'GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
        )
    
    # Retrieve OAuth client credentials from environment
    google_client_id: str = os.getenv('OAUTH_CLIENT_ID', '')
    google_client_secret: str = os.getenv('OAUTH_CLIENT_SECRET', '')

    if not google_client_id or not google_client_secret:
        logger.error("Missing OAUTH_CLIENT_ID or OAUTH_CLIENT_SECRET environment variables. OAuth will not function correctly.")
        raise ValueError("OAuth client credentials are not set.")

    greeter_agent, greeter_agent_card = create_greeter_agent(host, port) # Renamed _ to greeter_agent_card
    calendar_agent, calendar_agent_card = create_calendar_agent(
        host,
        port,
        client_id=google_client_id, # Use retrieved variable
        client_secret=google_client_secret, # Use retrieved variable
    )
    orchestrator_agent, orchestrator_agent_card = create_orchestrator_agent(
        host, port, sub_agents=[greeter_agent, calendar_agent]
    )

    runner: Runner = Runner(
        app_name=orchestrator_agent_card.name,
        agent=orchestrator_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor: ADKAgentExecutor = ADKAgentExecutor(runner, calendar_agent_card)

    async def handle_auth(request: Request) -> PlainTextResponse:
        state_param: str = str(request.query_params.get('state', ''))
        url_param: str = str(request.url)
        await agent_executor.on_auth_callback(state_param, url_param)
        return PlainTextResponse('Authentication successful.')

    request_handler: DefaultRequestHandler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    a2a_app: A2AStarletteApplication = A2AStarletteApplication(
        agent_card=orchestrator_agent_card, http_handler=request_handler
    )
    routes: List[Route] = a2a_app.routes()
    routes.append(
        Route(
            path='/authenticate',
            methods=['GET'],
            endpoint=handle_auth,
        )
    )
    app: Starlette = Starlette(
        routes=routes,
        middleware=[
            Middleware(
                AuthenticationMiddleware, backend=InsecureJWTAuthBackend()
            )
        ],
    )

    uvicorn.run(app, host=host, port=port)

if __name__ == '__main__':
    main()
