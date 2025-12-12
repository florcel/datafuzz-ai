"""Contract payload generation and fuzzing utilities."""
import random
import string
from core.parser import resolve_type


def gen_value_for_schema(schema):
    """Generate a valid example value for a JSON schema.
    
    Recursively traverses the schema and creates appropriate default values
    for each type (string, number, boolean, enum, object).
    """
    resolved = resolve_type(schema) or {}
    value_type = resolved.get("type")
    
    if value_type == "string":
        return "ok"
    elif value_type == "number":
        return 1
    elif value_type == "boolean":
        return True
    elif value_type == "enum":
        enum_values = resolved.get("values", [])
        return enum_values[0] if enum_values else "INVALID"
    elif value_type == "object":
        result = {}
        properties = _get_object_properties(resolved, schema)
        
        for prop_name, prop_schema in properties.items():
            result[prop_name] = gen_value_for_schema(prop_schema)
        return result
    
    return None


def gen_valid_payload(schema):
    """Generate a valid payload from the schema."""
    return gen_value_for_schema(schema)


def _get_object_properties(resolved, original_schema):
    """Extract properties dict from resolved or original schema.
    
    Tries resolved schema first (preferred), then falls back to original schema,
    to handle cases where schema resolution adds standard fields.
    """
    # Try resolved schema first
    if isinstance(resolved, dict) and "properties" in resolved:
        props = resolved.get("properties")
        if props:
            return props
    
    # Fall back to original schema
    if isinstance(original_schema, dict):
        props = original_schema.get("properties")
        if props:
            return props
    
    return {}


def _create_mutation_for_enum(valid_payload, prop_name):
    """Create a mutation with an invalid enum value."""
    mutation = dict(valid_payload) if isinstance(valid_payload, dict) else {}
    mutation[prop_name] = "INVALID_ENUM"
    return ("invalid_enum", mutation)


def _create_mutation_for_long_string(valid_payload, prop_name):
    """Create a mutation with an excessively long string (potential DoS)."""
    mutation = dict(valid_payload) if isinstance(valid_payload, dict) else {}
    mutation[prop_name] = "A" * 5000
    return ("long_string", mutation)


def _create_mutation_for_unicode(valid_payload, prop_name):
    """Create a mutation with unusual Unicode characters."""
    mutation = dict(valid_payload) if isinstance(valid_payload, dict) else {}
    mutation[prop_name] = "🤖漢字\u200b"
    return ("weird_unicode", mutation)


def gen_invalid_mutations(schema):
    """Generate invalid payload mutations for fuzzing.
    
    Creates several types of invalid payloads:
    - missing required fields
    - invalid enum values
    - excessively long strings
    - unusual Unicode sequences
    
    These are used to test how the API handles malformed requests.
    """
    try:
        # Allow tests to monkeypatch the payload generator
        import engines.contract.generator as parent_gen
        valid_payload = getattr(parent_gen, "gen_valid_payload", gen_valid_payload)(schema)
    except Exception:
        valid_payload = gen_valid_payload(schema)
    
    mutations = []
    resolved = resolve_type(schema) or {}
    
    if resolved.get("type") != "object":
        return mutations
    
    # Mutation 1: Remove required fields
    required_fields = resolved.get("required", []) or []
    if required_fields and isinstance(valid_payload, dict):
        missing_req = dict(valid_payload)
        for field in required_fields:
            missing_req.pop(field, None)
        mutations.append(("missing_required", missing_req))
    
    # Get properties for remaining mutations
    properties = _get_object_properties(resolved, schema)
    if not properties:
        return mutations
    
    # Mutation 2: Invalid enum values
    for prop_name, prop_schema in properties.items():
        prop_resolved = resolve_type(prop_schema) or {}
        if prop_resolved.get("type") == "enum":
            mutations.append(_create_mutation_for_enum(valid_payload, prop_name))
    
    # Mutation 3: Excessively long strings
    for prop_name, prop_schema in properties.items():
        prop_resolved = resolve_type(prop_schema) or {}
        if prop_resolved.get("type") == "string":
            mutations.append(_create_mutation_for_long_string(valid_payload, prop_name))
            break  # Only one per payload
    
    # Mutation 4: Unusual Unicode
    for prop_name, prop_schema in properties.items():
        prop_resolved = resolve_type(prop_schema) or {}
        if prop_resolved.get("type") == "string":
            mutations.append(_create_mutation_for_unicode(valid_payload, prop_name))
            break  # Only one per payload
    
    return mutations
