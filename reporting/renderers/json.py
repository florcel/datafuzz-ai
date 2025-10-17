from typing import Any, Dict
import json

def render_json(data: Dict[str, Any]) -> str:
    """Render the given data as a JSON string."""
    return json.dumps(data, indent=4)