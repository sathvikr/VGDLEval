import json
import re
import logging

logger = logging.getLogger(__name__)

KEY_MAPPING = {
    "UP": 38,
    "DOWN": 40,
    "LEFT": 37,
    "RIGHT": 39,
    "SPACE": 32,
    "NOOP": None,
}

def parse_actions(response_text: str) -> list[int]:
    """Extract actions from LLM response."""
    match = re.search(r'<keys>(.*?)</keys>', response_text, re.DOTALL)
    if match:
        try:
            actions_str = match.group(1).strip()
            # Using json.loads to safely parse the list string
            # The LLM is expected to output valid JSON list: ["UP", "DOWN", ...]
            # Only replace single quotes with double quotes if necessary
            if "'" in actions_str and '"' not in actions_str:
                actions_str = actions_str.replace("'", '"')
            
            action_names = json.loads(actions_str)
            
            actions = []
            for name in action_names:
                name = name.upper()
                if name in KEY_MAPPING:
                    # Skip NOOP actions in the execution list (handled as wait)
                    actions.append(KEY_MAPPING[name])
                else:
                    logger.warning(f"Unknown action: {name}")
            return actions
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse actions JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing actions: {e}")
            return []
    else:
        logger.warning("No <actions> tag found in response")
        return []

