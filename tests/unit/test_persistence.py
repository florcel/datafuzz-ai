import importlib
import sys
import sqlite3

import pytest

def _reload_module(name):
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)

def test_init_db_and_persist_run_and_result(tmp_path, monkeypatch):
    # use a temp sqlite file for isolation
    db_path = tmp_path / "test_datafuzz.db"
    monkeypatch.setenv("DATAFUZZ_DATABASE_URL", f"sqlite:///{db_path}")

    # ensure modules pick up the env var by reloading
    _reload_module("storage.db")
    _reload_module("storage.models")
    _reload_module("storage.repository")

    from storage.db import init_db, SessionLocal
    from storage.repository import create_run, save_result
    from storage.models import Result

    # init and assert file created
    init_db()
    assert db_path.exists()

    # create run and save a result
    run = create_run(name="unit-test-run")
    assert run.id is not None
    res = save_result(
        run_id=run.id,
        endpoint="/users",
        method="post",
        payload={"name": "alice"},
        status_code=201,
        latency=0.123,
        error=None,
    )
    assert res.id is not None
    assert res.run_id == run.id

    # verify via a fresh session
    session = SessionLocal()
    try:
        q = session.query(Result).filter_by(run_id=run.id).all()
        assert len(q) == 1
        r = q[0]
        assert r.endpoint == "/users"
        assert r.status_code == 201
        assert isinstance(r.payload, dict)
    finally:
        session.close()

def test_multiple_results_same_run(tmp_path, monkeypatch):
    db_path = tmp_path / "test_datafuzz2.db"
    monkeypatch.setenv("DATAFUZZ_DATABASE_URL", f"sqlite:///{db_path}")

    _reload_module("storage.db")
    _reload_module("storage.models")
    _reload_module("storage.repository")

    from storage.db import init_db, SessionLocal
    from storage.repository import create_run, save_result
    from storage.models import Result

    init_db()
    run = create_run(name="multi-result-run")
    assert run.id is not None

    for i in range(3):
        save_result(
            run_id=run.id,
            endpoint="/items",
            method="get",
            payload={"i": i},
            status_code=200,
            latency=0.01 * i,
            error=None,
        )

    session = SessionLocal()
    try:
        rows = session.query(Result).filter_by(run_id=run.id).count()
        assert rows == 3
    finally:
        session.close()