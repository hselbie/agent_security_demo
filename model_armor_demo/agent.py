import os
import logging
from typing import Optional

from google.adk.agents import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.cloud import modelarmor_v1
from google.genai import types as genai_types

# Set the GOOGLE_CLOUD_PROJECT environment variable
GOOGLE_CLOUD_PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
if not GOOGLE_CLOUD_PROJECT_ID:
    logger.error("GOOGLE_CLOUD_PROJECT environment variable not set. Model Armor demo may not function correctly.")

GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
TEMPLATE_ID = "ma-all-low"

# Worker Agent
worker_agent = Agent(
    name="worker_agent",
    model="gemini-2.5-flash",
    instruction="You are a worker agent. You can handle sensitive data.",
    description="An agent that can handle sensitive data.",
    # tools=[handle_sensitive_data],
)

# Model Armor Callback
async def model_armor_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Intercepts and blocks requests containing sensitive information."""
    if not GOOGLE_CLOUD_PROJECT_ID:
        logger.warning("Model Armor skipped: GOOGLE_CLOUD_PROJECT environment variable not set.")
        return None # Allow request to proceed if project ID is missing

    try:
        # Use GOOGLE_CLOUD_LOCATION for the API endpoint
        api_endpoint = f"modelarmor.{GOOGLE_CLOUD_LOCATION}.rep.googleapis.com"
        client = modelarmor_v1.ModelArmorAsyncClient(client_options={"api_endpoint": api_endpoint})

        # Assuming the last content part is the user's text prompt
        prompt_text = ""
        if llm_request.contents and llm_request.contents[-1].parts:
            for part in llm_request.contents[-1].parts:
                if part.text:
                    prompt_text += part.text
        
        if not prompt_text:
            logger.warning("Model Armor received empty prompt text.")
            return None

        prompt_data = modelarmor_v1.DataItem(text=prompt_text)
        request = modelarmor_v1.SanitizeUserPromptRequest(
            name=f"projects/{GOOGLE_CLOUD_PROJECT_ID}/locations/{GOOGLE_CLOUD_LOCATION}/templates/{TEMPLATE_ID}",
            user_prompt_data=prompt_data,
        )
        response = await client.sanitize_user_prompt(request=request)

        if response.sanitization_result.filter_match_state == 2: # FilterMatchState.BLOCKED
            logger.warning(f"Model Armor blocked request due to sensitive information. Prompt: '{prompt_text}'")
            return LlmResponse(
                content=genai_types.Content(
                    parts=[
                        genai_types.Part(
                            text="Blocked by Model Armor: Request contains sensitive information."
                        )
                    ]
                )
            )
        logger.info(f"Model Armor scan successful. Prompt: '{prompt_text[:50]}...' Status: {response.sanitization_result.filter_match_state}")
        return None # Allow request to proceed
    except Exception as e:
        logger.error(f"Error during Model Armor sanitization: {e}")
        # Depending on policy, you might block here or allow to proceed
        return LlmResponse(
            content=genai_types.Content(
                parts=[
                    genai_types.Part(
                        text="An error occurred during safety check. Please try again or contact support."
                    )
                ]
            )
        )

# Supervisor Agent
supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-2.5-flash",
    instruction="You are a supervisor agent. You delegate tasks to the worker agent.",
    description="An agent that delegates tasks.",
    sub_agents=[worker_agent],
    before_model_callback=model_armor_callback,
)

root_agent: Agent = supervisor_agent
