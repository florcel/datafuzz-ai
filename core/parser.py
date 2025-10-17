from pathlib import Path
import json
import yaml
try:
    from openapi_spec_validator import validate_spec
except Exception:
    # fallback: no-op validator si la dependencia no está instalada
    def validate_spec(_):
        return None

def load_spec(path: str):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if p.suffix in (".yml", ".yaml") else json.loads(text)
    validate_spec(data)
    return data

def get_schema_for_path(spec: dict, endpoint: str, method: str):
    """Return requestBody schema for application/json or None."""
    paths = spec.get("paths", {})
    m = paths.get(endpoint, {}).get(method.lower(), {})
    rb = m.get("requestBody", {})
    content = rb.get("content", {}).get("application/json", {})
    return content.get("schema")

def resolve_type(schema: dict):
    """Resolve primitive types: string/number/boolean/enum, and shallow objects."""
    if not schema:
        return {"type": "object"}
    if "enum" in schema:
        return {"type": "enum", "values": schema["enum"]}
    t = schema.get("type")
    if t == "string":
        return {"type": "string"}
    if t in ("integer", "number"):
        return {"type": "number"}
    if t == "boolean":
        return {"type": "boolean"}
    if t == "object":
        props = schema.get("properties", {})
        return {"type": "object", "properties": props, "required": schema.get("required", [])}
    return {"type": t}