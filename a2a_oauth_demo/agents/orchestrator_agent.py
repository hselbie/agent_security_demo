import os
import logging
from typing import List, Tuple

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Configure logging
logger = logging.getLogger(__name__)

def create_orchestrator_agent(
    host: str, port: int, sub_agents: List[LlmAgent]
) -> Tuple[LlmAgent, AgentCard]: # Explicit return type hint
    """Constructs the ADK agent."""
    LITELLM_MODEL: str = os.getenv('LITELLM_MODEL', 'gemini/gemini-2.0-flash-001') # Use env var
    agent: LlmAgent = LlmAgent(
        model=LiteLlm(model=LITELLM_MODEL),
        name='orchestrator_agent',
        description='An agent that can route requests to other agents',
        instruction='''
You are an agent that routes requests to other agents.

Examine the user's query and the descriptions of your sub-agents and route the request to the appropriate agent.
''',
        sub_agents=sub_agents,
    )
    logger.info(f"Orchestrator Agent created with model: '{LITELLM_MODEL}'")

    agent_card: AgentCard = AgentCard(
        name='Orchestrator Agent',
        description='An agent that can route requests to other agents',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id='orchestrate',
                name='Orchestrate',
                description='Routes requests to other agents',
                tags=['orchestration'],
                examples=[
                    'Hello',
                    'Am I free from 10am to 11am tomorrow?',
                ],
            )
        ],
    )
    logger.info(f"Orchestrator AgentCard created for URL: {agent_card.url}")    return agent, agent_card
