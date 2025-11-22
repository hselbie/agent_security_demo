import json
import logging
from typing import Dict, Any

from google.adk.tools import ToolContext

# Configure logging
logger = logging.getLogger(__name__)


def get_datastore_content(datastore_name: str, access_level: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Fetches content from the specified datastore based on the user's access level.

    Args:
        datastore_name (str): The name of the datastore to access (e.g., 'marketing', 'sales').
        access_level (str): The user's access level ('employee' or 'manager').
        tool_context (ToolContext): The tool context.

    Returns:
        dict: The datastore content or an error message.
    """
    logger.info(f"Attempting to fetch content from datastore: '{datastore_name}' with access level: '{access_level}'")
    try:
        file_path = f'abac_demo/data/{datastore_name}_data.json'
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if access_level == 'manager':
            logger.info(f"Access granted for manager level for datastore: '{datastore_name}'")
            return {"status": "success", "data": data['full']}
        elif access_level == 'employee':
            logger.info(f"Access granted for employee level for datastore: '{datastore_name}'")
            return {"status": "success", "data": data['limited']}
        else:
            logger.warning(f"Invalid access level '{access_level}' provided for datastore: '{datastore_name}'")
            return {"status": "error", "message": "Invalid access level."}

    except FileNotFoundError:
        logger.error(f"Datastore file '{file_path}' not found for datastore: '{datastore_name}'")
        return {"status": "error", "message": f"Datastore '{datastore_name}' not found."}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from '{file_path}': {e}")
        return {"status": "error", "message": f"Error reading datastore '{datastore_name}': Invalid JSON format."}
    except KeyError as e:
        logger.error(f"Missing expected key in datastore '{file_path}': {e}")
        return {"status": "error", "message": f"Error in datastore '{datastore_name}': Missing expected data structure."}
    except Exception as e:
        logger.error(f"An unexpected error occurred while accessing datastore '{datastore_name}': {e}")
        return {"status": "error", "message": str(e)}
