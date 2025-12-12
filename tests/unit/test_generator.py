from engines.contract import generator as gen

def test_gen_simple():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
    val = gen.gen_valid_payload(schema)
    assert isinstance(val, dict)
    assert "name" in val

def test_mutations_exist():
    schema = {"type": "object", "properties": {"role": {"type": "string", "enum": ["a","b"]}}, "required": ["role"]}
    muts = gen.gen_invalid_mutations(schema)
    names = [name for name, _ in muts]
    assert "missing_required" in names or "invalid_enum" in names
from engines.contract import generator as gen

def test_gen_simple():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
    val = gen.gen_valid_payload(schema)
    assert isinstance(val, dict)
    assert "name" in val

def test_mutations_exist():
    schema = {"type": "object", "properties": {"role": {"type": "string", "enum": ["a","b"]}}, "required": ["role"]}
    muts = gen.gen_invalid_mutations(schema)
    names = [name for name, _ in muts]
    assert "missing_required" in names or "invalid_enum" in names