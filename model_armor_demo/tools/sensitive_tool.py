"""A tool for handling sensitive data."""
import logging
from typing import Dict

# Configure logging
logger = logging.getLogger(__name__)

def handle_sensitive_data(data: str) -> Dict[str, str]:
    """Handles sensitive data.

    Args:
        data (str): The sensitive data to handle.

    Returns:
        dict: A dictionary with the status of the operation.
    """
    logger.info(f"handle_sensitive_data tool called with data: '{data}'")
    if "sensitive" in data:
        logger.warning(f"Sensitive data detected: '{data}'. Blocking operation.")
        return {"status": "error", "message": "This data is too sensitive to handle."}
    logger.info(f"Data handled successfully: '{data}'")
    return {"status": "success", "data": f"Successfully handled data: {data}"}
