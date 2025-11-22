import os
import logging
from typing import Tuple

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Configure logging
logger = logging.getLogger(__name__)

def create_greeter_agent(host: str, port: int) -> Tuple[LlmAgent, AgentCard]: # Explicit return type hint
    """Constructs the ADK agent."""
    LITELLM_MODEL: str = os.getenv('LITELLM_MODEL', 'gemini/gemini-2.0-flash-001') # Use env var
    agent: LlmAgent = LlmAgent(
        model=LiteLlm(model=LITELLM_MODEL),
        name='greeter_agent',
        description='An agent that can greet users',
        instruction='You are an agent that greets the user.',
    )
    logger.info(f"Greeter Agent created with model: '{LITELLM_MODEL}'")

    skill: AgentSkill = AgentSkill(
        id='greet',
        name='Greet',
        description='Greets the user',
        tags=['greeting'],
        examples=['Hello'],
    )

    agent_card: AgentCard = AgentCard(
        name='Greeter Agent',
        description='An agent that can greet users',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    logger.info(f"Greeter AgentCard created for URL: {agent_card.url}")
    return agent, agent_card
