import random
import string
from core.parser import resolve_type

def gen_value_for_schema(schema):
    r = resolve_type(schema)
    t = r["type"]
    if t == "string":
        return "ok"
    if t == "number":
        return 1
    if t == "boolean":
        return True
    if t == "enum":
        vals = r.get("values", [])
        return vals[0] if vals else "INVALID"
    if t == "object":
        out = {}
        for k, prop in r.get("properties", {}).items():
            out[k] = gen_value_for_schema(prop)
        return out
    return None

def gen_valid_payload(schema):
    return gen_value_for_schema(schema)

def gen_invalid_mutations(schema):
    """Return list of tuples (name, payload) with simple invalid mutations."""
    valid = gen_valid_payload(schema)
    muts = []
    r = resolve_type(schema)
    if r["type"] == "object":
        # missing required
        req = r.get("required", [])
        if req:
            p = dict(valid) if isinstance(valid, dict) else valid
            for k in req:
                p.pop(k, None)
            muts.append(("missing_required", p))
        # invalid enum
        for k, prop in r.get("properties", {}).items():
            pr = resolve_type(prop)
            if pr["type"] == "enum":
                bad = dict(valid)
                bad[k] = "INVALID_ENUM"
                muts.append(("invalid_enum", bad))
        # long string
        for k, prop in r.get("properties", {}).items():
            pr = resolve_type(prop)
            if pr["type"] == "string":
                longp = dict(valid)
                longp[k] = "A" * 5000
                muts.append(("long_string", longp))
                break
        # weird unicode
        for k, prop in r.get("properties", {}).items():
            pr = resolve_type(prop)
            if pr["type"] == "string":
                uni = dict(valid)
                uni[k] = "🤖漢字\u200b"
                muts.append(("weird_unicode", uni))
                break
    return muts