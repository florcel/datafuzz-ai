import importlib
import sys
import asyncio
import json

import pytest

def _reload_module(name):
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)

@pytest.mark.parametrize("n", [3])
def test_run_parallel_persists_results(tmp_path, monkeypatch, capsys, n):
    # use a temp sqlite file for isolation
    db_path = tmp_path / "rp_test.db"
    monkeypatch.setenv("DATAFUZZ_DATABASE_URL", f"sqlite:///{db_path}")

    # reload storage modules so engine uses the tmp DB
    _reload_module("storage.db")
    _reload_module("storage.models")
    _reload_module("storage.repository")

    # reload cli to bind to the refreshed repository/db
    _reload_module("apps.cli.cli")

    # shallow mocks for parser/generator
    import apps.cli.cli as cli_mod
    from core import parser as core_parser
    from engines import contract as contract_mod

    monkeypatch.setattr(core_parser, "load_spec", lambda spec: {"dummy": True})
    monkeypatch.setattr(core_parser, "get_schema_for_path", lambda spec, endpoint, method: {"type": "object"})
    monkeypatch.setattr(contract_mod.generator, "gen_valid_payload", lambda schema: {"name": "alice", "role": "admin"})

    # fake async runner result (same length as n)
    async def fake_run_concurrent(method, url, payloads, concurrency, timeout, retries):
        results = []
        for _ in payloads:
            results.append({"status_code": 201, "latency": 0.05, "body": '{"id":0,"name":"alice","role":"admin"}'})
        return {"summary": {"total": len(results)}, "results": results}

    # patch the run_concurrent used by cli
    monkeypatch.setattr(cli_mod, "run_concurrent", fake_run_concurrent)

    # import DB session and models
    from storage.db import SessionLocal, init_db
    from storage.models import Result

    # call the CLI function directly
    init_db()
    cli_mod.run_parallel(
        spec="specs/examples/openapi.yaml",
        endpoint="/users",
        method="post",
        base_url="http://127.0.0.1:4010",
        n=n,
        concurrency=2,
        timeout=1.0,
        retries=0,
        run_name="test-parallel",
    )

    # capture printed summary
    captured = capsys.readouterr()
    assert '"total": 3' in captured.out or '"total": 3' in captured.err or "run-parallel complete" in captured.out

    # verify results persisted
    session = SessionLocal()
    try:
        rows = session.query(Result).count()
        assert rows == n
        first = session.query(Result).first()
        assert first.endpoint == "/users"
        assert first.status_code == 201
        assert isinstance(first.payload, dict)
    finally:
        session.close()