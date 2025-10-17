import random

_EDGE_STRINGS = ["", " ", "a"*256, "こんにちは", "👍", "\u202Ertl"]
_EDGE_NUMBERS = [0, -1, 1, 2**31-1, 3.14159]

def _synth(schema):
    if not schema: return None
    t = schema.get("type")
    if t == "object":
        out = {}
        props = schema.get("properties", {})
        for k, s in props.items():
            out[k] = _synth(s)
        return out
    if t == "array":
        it = schema.get("items", {})
        return [_synth(it) for _ in range(random.randint(0, 3))]
    if t == "string":
        enum = schema.get("enum")
        if enum: return random.choice(enum)
        return random.choice(["ok", "test"] + _EDGE_STRINGS)
    if t == "integer":
        return random.choice(_EDGE_NUMBERS)
    if t == "number":
        return random.choice(_EDGE_NUMBERS)
    if t == "boolean":
        return random.choice([True, False])
    return None

def _mutate_invalid(payload, schema):
    # quita un required (si hay) para generar casos inválidos simples
    if isinstance(payload, dict) and schema and schema.get("required"):
        q = payload.copy()
        drop = random.choice(schema["required"])
        q.pop(drop, None)
        return q
    return payload

def make_payloads(schema: dict, n: int = 50) -> list[dict]:
    base = [_synth(schema) for _ in range(max(1, n//2))]
    invalids = [_mutate_invalid(p, schema) for p in base]
    return base + invalids
