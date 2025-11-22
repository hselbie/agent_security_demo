
import logging
from typing import Optional

from google.adk.agents import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types as genai_types
from model_armor_demo.tools.sensitive_tool import handle_sensitive_data

# Worker Agent
worker_agent = Agent(
    name="worker_agent",
    model="gemini-2.5-flash",
    instruction="You are a worker agent. You can handle sensitive data.",
    description="An agent that can handle sensitive data.",
    tools=[handle_sensitive_data],
)

# Prompt Inspection Callback (Renamed from model_armor_callback for clarity)
def prompt_inspection_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Intercepts and blocks requests containing the keyword 'sensitive'."""
    prompt_text = ""
    if llm_request.contents and llm_request.contents[-1].parts:
        for part in llm_request.contents[-1].parts:
            if part.text:
                prompt_text += part.text

    if "sensitive" in prompt_text.lower(): # Case-insensitive check
        logger.warning(f"Prompt inspection blocked request due to 'sensitive' keyword. Prompt: '{prompt_text}'")
        return LlmResponse(
            content=genai_types.Content(
                parts=[
                    genai_types.Part(
                        text="Blocked by Prompt Inspection: Request contains sensitive information."
                    )
                ]
            )
        )
    logger.info(f"Prompt inspection passed for prompt: '{prompt_text[:50]}...'")
    return None

# Supervisor Agent
supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-2.5-flash",
    instruction="You are a supervisor agent. You delegate tasks to the worker agent.",
    description="An agent that delegates tasks.",
    sub_agents=[worker_agent],
    before_model_callback=prompt_inspection_callback, # Updated callback name
)

root_agent: Agent = supervisor_agent
