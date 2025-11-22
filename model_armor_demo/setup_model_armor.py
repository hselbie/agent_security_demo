
import os
import logging
from google.api_core import exceptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from google.cloud import modelarmor_v1

# --- Configuration ---
# These values are used to create the template.
PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "YOUR_PROJECT_ID")
LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
TEMPLATE_ID: str = "ma-all-low" # The template ID your agent uses

def create_model_armor_template():
    """
    Connects to the Model Armor API and creates a predefined template.

    This function defines the configuration for the 'ma-all-low' template,
    which includes a comprehensive set of filters for prompt and response
    sanitization at a low confidence threshold (i.e., high sensitivity).

    You only need to run this script once per project.
    """
    if PROJECT_ID == "YOUR_PROJECT_ID" or not PROJECT_ID:
        logger.error("PROJECT_ID is not set or is still the placeholder 'YOUR_PROJECT_ID'. "
                     "Please set the GOOGLE_CLOUD_PROJECT_ID environment variable.")
        return

    logger.info(f"Attempting to create template '{TEMPLATE_ID}' in project '{PROJECT_ID}'...")

    try:
        # Instantiate the Model Armor client
        # Using a synchronous client here for a simple, one-off script.
        client = modelarmor_v1.ModelArmorClient(
            transport="rest",
            client_options={"api_endpoint": f"modelarmor.{LOCATION}.rep.googleapis.com"}
        )

        # Define the full structure of the template
        template_config = {
            "filter_config": {
                "rai_settings": {
                    "rai_filters": [
                        {"filter_type": "HATE_SPEECH", "confidence_level": "LOW_AND_ABOVE"},
                        {"filter_type": "SEXUALLY_EXPLICIT", "confidence_level": "LOW_AND_ABOVE"},
                        {"filter_type": "HARASSMENT", "confidence_level": "LOW_AND_ABOVE"},
                        {"filter_type": "DANGEROUS", "confidence_level": "LOW_AND_ABOVE"},
                    ]
                },
                "pi_and_jailbreak_filter_settings": {
                    "filter_enforcement": "ENABLED",
                    "confidence_level": "LOW_AND_ABOVE",
                },
                "malicious_uri_filter_settings": {"filter_enforcement": "ENABLED"},
                "sdp_settings": {"basic_config": {"filter_enforcement": "ENABLED"}},
            },
            "template_metadata": {
                "log_template_operations": True,
                "log_sanitize_operations": True,
            },
        }

        # Construct the request
        request = modelarmor_v1.CreateTemplateRequest(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            template_id=TEMPLATE_ID,
            template=template_config,
        )

        # Make the API call to create the template
        response = client.create_template(request=request)

        logger.info("-" * 40)
        logger.info(f"✅ Successfully created template '{TEMPLATE_ID}'.")
        logger.info("You can now run your agent.")
        logger.info("-" * 40)
        logger.info("Template details:")
        logger.info(response)

    except exceptions.AlreadyExists:
        logger.info("-" * 40)
        logger.info(f"✅ Template '{TEMPLATE_ID}' already exists in project '{PROJECT_ID}'.")
        logger.info("No action needed. You can run your agent.")
        logger.info("-" * 40)
    except exceptions.PermissionDenied as e:
        logger.error("-" * 40)
        logger.error("❌ ERROR: Permission Denied.")
        logger.error("Please ensure you have the 'Model Armor Admin' (roles/modelarmor.admin) role")
        logger.error(f"in the '{PROJECT_ID}' project and that the Model Armor API is enabled.")
        logger.error(f"Full error: {e}")
        logger.error("-" * 40)
    except Exception as e:
        logger.error("-" * 40)
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.error("-" * 40)
