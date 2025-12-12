"""OpenAPI specification parsing and schema resolution."""
from pathlib import Path
import json
import yaml

try:
    from openapi_spec_validator import validate_spec
except ImportError:
    # Fallback: no-op validator if dependency is not installed
    def validate_spec(_):
        return None


def load_spec(path: str):
    """Load OpenAPI specification from YAML or JSON file.
    
    Args:
        path: Path to the spec file (.yaml, .yml, or .json)
    
    Returns:
        The parsed OpenAPI specification dict
    """
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    # Detect format from file extension
    if file_path.suffix in (".yml", ".yaml"):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    
    # Validate spec format
    validate_spec(data)
    return data


def get_schema_for_path(spec: dict, endpoint: str, method: str):
    """Extract the request body schema for a specific endpoint and HTTP method."""
    paths = spec.get("paths", {})
    if endpoint not in paths:
        return None
    
    path_item = paths[endpoint]
    method_lower = method.lower()
    
    if method_lower not in path_item:
        return None
    
    operation = path_item[method_lower]
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    
    return json_content.get("schema")


def resolve_type(schema: dict):
    """Resolve and normalize a JSON schema to a simplified form."""
    if not schema:
        return {"type": "object"}
    
    # Handle enum type first (overrides any other type)
    if "enum" in schema:
        return {
            "type": "enum",
            "values": schema["enum"]
        }
    
    schema_type = schema.get("type")
    
    # Normalize numeric types
    if schema_type in ("integer", "number"):
        return {"type": "number"}
    
    # Simple scalar types
    if schema_type in ("string", "boolean"):
        return {"type": schema_type}
    
    # Object type: include properties and required fields
    if schema_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        return {
            "type": "object",
            "properties": properties if isinstance(properties, dict) else {},
            "required": required if isinstance(required, list) else []
        }
    
    # Fallback for unknown types
    return {"type": schema_type or "object"}
