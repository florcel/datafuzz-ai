from pydantic import BaseModel
import yaml, hashlib

class Endpoint(BaseModel):
    method: str
    path: str
    schema: dict | None = None

def load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_endpoint(spec: dict, path: str, method: str = "post") -> Endpoint:
    m = method.lower()
    item = spec["paths"][path][m]
    schema = (
        item.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema")
    )
    return Endpoint(method=m, path=path, schema=schema)

def spec_hash(spec: dict) -> str:
    raw = yaml.safe_dump(spec).encode()
    return hashlib.sha256(raw).hexdigest()[:12]
