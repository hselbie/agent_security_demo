import datetime
import os
import logging
from typing import List, Tuple

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AuthorizationCodeOAuthFlow,
    OAuth2SecurityScheme,
    OAuthFlows,
    SecurityScheme,
)
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.google_api_tool import (
    CalendarToolset,
)

# Configure logging
logger = logging.getLogger(__name__)

def create_calendar_agent(
    host: str, port: int, client_id: str, client_secret: str
) -> Tuple[LlmAgent, AgentCard]: # Explicit return type hint
    """Constructs the ADK agent."""
    LITELLM_MODEL: str = os.getenv('LITELLM_MODEL', 'gemini/gemini-2.0-flash-001')
    CALENDAR_SCOPES_STR: str = os.getenv('CALENDAR_SCOPES', 'https://www.googleapis.com/auth/calendar')
    CALENDAR_SCOPES_LIST: List[str] = CALENDAR_SCOPES_STR.split() if CALENDAR_SCOPES_STR else ['https://www.googleapis.com/auth/calendar']

    toolset: CalendarToolset = CalendarToolset(client_id=client_id, client_secret=client_secret)
    agent: LlmAgent = LlmAgent(
        model=LiteLlm(model=LITELLM_MODEL),
        name='calendar_agent',
        description="An agent that can help manage a user's calendar",
        instruction=f"""\nYou are an agent that can help manage a user's calendar.\n\nUsers will request information about the state of their calendar or to make changes to\ntheir calendar. Use the provided tools for interacting with the calendar API.\n\nIf not specified, assume the calendar the user wants is the 'primary' calendar.\n\nWhen using the Calendar API tools, use well-formed RFC3339 timestamps.\n\nToday is {datetime.date.today()}\n""", # Changed to datetime.date.today()
        tools=[toolset],
    )
    logger.info(f"Calendar Agent created with model: '{LITELLM_MODEL}' and scopes: '{CALENDAR_SCOPES_STR}'")

    skill = AgentSkill(
        id='check_availability',
        name='Check Availability',
        description="Checks a user's availability for a time using their Google Calendar",
        tags=['calendar'],
        examples=['Am I free from 10am to 11am tomorrow?'],
    )

    # Define OAuth2 security scheme.
    OAUTH_SCHEME_NAME = 'CalendarGoogleOAuth'
    oauth_scheme: OAuth2SecurityScheme = OAuth2SecurityScheme(
        type='oauth2',
        description='OAuth2 for Google Calendar API',
        flows=OAuthFlows(
            authorization_code=AuthorizationCodeOAuthFlow(
                authorization_url='https://accounts.google.com/o/oauth2/auth',
                token_url='https://oauth2.googleapis.com/token',
                scopes={
                    scope: f'Access Google Calendar with {scope}' for scope in CALENDAR_SCOPES_LIST # Use dynamic scopes
                },
            )
        ),
    )

    # Update the AgentCard to include the 'security_schemes' and 'security' fields.
    agent_card: AgentCard = AgentCard(
        name='Calendar Agent',
        description="An agent that can manage a user's calendar",
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        security_schemes={OAUTH_SCHEME_NAME: SecurityScheme(root=oauth_scheme)},
        # Declare that this scheme is required to use the agent's skills
        security=[
            {OAUTH_SCHEME_NAME: CALENDAR_SCOPES_LIST} # Use dynamic scopes
        ],
    )
    logger.info(f"Calendar AgentCard created with security schemes for {OAUTH_SCHEME_NAME}")
    return agent, agent_card
