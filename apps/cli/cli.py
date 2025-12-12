import typer
from core import parser as core_parser
from engines.contract import generator as contract_gen
from apps.runner.http_runner import send_request
from apps.reporting.renderers.datafuzz import render_report
import json
import pathlib
import asyncio

# persistence
from storage.db import init_db
from storage.repository import create_run, save_result, get_latest_run, get_results_for_run

# async runner
from apps.runner.async_runner import run_concurrent

app = typer.Typer()

@app.command()
def gen(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    n: int = typer.Option(10, "--n", help="Number of samples"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock")
):
    # TODO: agregar soporte para generar payloads para múltiples endpoints en paralelo
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, "post")
    samples = [contract_gen.gen_valid_payload(schema) for _ in range(n)]
    out = pathlib.Path("reports/samples").resolve()
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "payloads.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f"generated {len(samples)} payloads -> {out / 'payloads.json'}")

@app.command()
def run(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    method: str = typer.Option("post", "--method", "-m", help="HTTP method"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock"),
    run_name: str | None = typer.Option(None, "--name", "-n", help="Optional run name")
):
    # FIXME: el manejo de errores de conexión necesita mejoras
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, method)

    # generate valid payload + invalid mutations from generator
    valid = contract_gen.gen_valid_payload(schema)
    muts = contract_gen.gen_invalid_mutations(schema)  # list of (name, payload)

    cases = [("valid", valid)] + muts
    url = base_url.rstrip("/") + endpoint

    run_obj = create_run(name=run_name)
    items = []

    for idx, (case_name, payload) in enumerate(cases, start=1):
        resp = send_request(method, url, json_body=payload)
        # persist
        save_result(
            run_id=run_obj.id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            status_code=resp.get("status_code"),
            latency=resp.get("latency"),
            error=resp.get("error"),
        )

        # map result/result string
        status = resp.get("status_code")
        latency_ms = None if resp.get("latency") is None else round(resp["latency"] * 1000, 1)

        if case_name == "valid":
            payload_type = "valid"
            if status and 200 <= status < 300:
                result_str = "OK"
            elif status:
                result_str = "FALLO"
            else:
                result_str = "ERROR"
            note = ""
        else:
            payload_type = "invalid"
            # tag invalid subtype in note/mutation
            mutation_name = case_name
            if status and 200 <= status < 300:
                # server accepted an invalid payload
                result_str = f"ACEPTADO (invalido:{mutation_name})"
            elif status and status >= 400:
                # server rejected invalid payload (expected)
                result_str = f"RECHAZADO (invalido:{mutation_name})"
            else:
                result_str = f"ERROR (invalido:{mutation_name})"
            note = mutation_name

        items.append({
            "id": idx,
            "payload_type": payload_type,
            "mutation": (None if case_name == "valid" else case_name),
            "status": str(status) if status is not None else "error",
            "latency_ms": latency_ms,
            "result": result_str,
            "note": note,
        })

    render_report(
        items=items,
        output_path="reports/samples/report.html",
        endpoint=endpoint,
        run_name=run_name,
        created_at=None
    )
    print(f"run complete (run_id={run_obj.id})")

@app.command()
def run_parallel(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    method: str = typer.Option("post", "--method", "-m", help="HTTP method"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock"),
    n: int = typer.Option(10, "--n", help="Number of requests to send"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Concurrency level"),
    timeout: float = typer.Option(5.0, "--timeout", help="Per-request timeout"),
    retries: int = typer.Option(1, "--retries", help="Retries per request"),
    run_name: str | None = typer.Option(None, "--name", "-n", help="Optional run name")
):
    # TODO: refactorizar esto, está medio repetitivo en algunos comandos
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, method)

    # build payload set mixing valid and invalid cases
    valid = contract_gen.gen_valid_payload(schema)
    muts = contract_gen.gen_invalid_mutations(schema)  # list of (name, payload)

    # create a list of payloads: prefer a mix (e.g., 60% valid, rest invalid cycles)
    payloads = []
    mutation_meta = []  # parallel list with metadata: ("valid", None) or ("invalid", mutation_name)
    for i in range(n):
        if muts and (i % 4 == 0):  # every 4th request use an invalid mutation (heuristic)
            name, p = muts[(i // 4) % len(muts)]
            payloads.append(p)
            mutation_meta.append(("invalid", name))
        else:
            payloads.append(valid)
            mutation_meta.append(("valid", None))

    url = base_url.rstrip("/") + endpoint
    run_obj = create_run(name=run_name)

    res = asyncio.run(run_concurrent(method, url, payloads, concurrency=concurrency, timeout=timeout, retries=retries))

    items = []
    for idx, (meta, payload, r) in enumerate(zip(mutation_meta, payloads, res["results"]), start=1):
        payload_type, mutation_name = meta
        save_result(
            run_id=run_obj.id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            status_code=r.get("status_code"),
            latency=r.get("latency"),
            error=r.get("error"),
        )

        status = r.get("status_code")
        latency_ms = None if r.get("latency") is None else round(r["latency"] * 1000, 1)

        if payload_type == "valid":
            if status and 200 <= status < 300:
                result_str = "OK"
            elif status:
                result_str = "FALLO"
            else:
                result_str = "ERROR"
            note = ""
        else:
            if status and 200 <= status < 300:
                result_str = f"ACEPTADO (invalido:{mutation_name})"
            elif status and status >= 400:
                result_str = f"RECHAZADO (invalido:{mutation_name})"
            else:
                result_str = f"ERROR (invalido:{mutation_name})"
            note = mutation_name

        items.append({
            "id": idx,
            "payload_type": payload_type,
            "mutation": mutation_name,
            "status": str(status) if status is not None else "error",
            "latency_ms": latency_ms,
            "result": result_str,
            "note": note,
        })

    render_report(
        items=items,
        output_path="reports/samples/report.html",
        endpoint=endpoint,
        run_name=run_name,
        created_at=None
    )
    print("run-parallel complete")
    print(json.dumps(res["summary"], indent=2, ensure_ascii=False))

@app.command()
def report(
    name: str | None = typer.Option(None, "--name", "-n", help="Optional run name to filter latest run"),
    out: str = typer.Option("reports/samples/report.html", "--out", help="Output HTML path"),
    slow_ms: int = typer.Option(900, "--slow-ms", help="Threshold for 'slow' classification in ms"),
):
    init_db()
    run_obj = get_latest_run(name=name)
    if not run_obj:
        typer.echo("No runs found. Execute a run first.")
        raise typer.Exit(code=1)

    results = get_results_for_run(run_obj.id)
    if not results:
        typer.echo("Selected run has no results.")
        raise typer.Exit(code=1)

    # Transform DB rows to items expected by render_report
    items = []
    for idx, r in enumerate(results, start=1):
        status = r.status_code
        latency_ms = None if r.latency is None else round(r.latency * 1000, 1)
        payload_type = "valid"  # default; we don't persist mutation type yet
        # We keep 'note' with error text or blank
        items.append({
            "id": idx,
            "payload_type": payload_type,
            "mutation": None,
            "status": str(status) if status is not None else "error",
            "latency_ms": latency_ms,
            "result": "",  # will be recomputed by renderer normalization
            "note": r.error or "",
        })

    render_report(
        items=items,
        output_path=out,
        endpoint=results[0].endpoint,
        run_name=run_obj.name,
        created_at=str(run_obj.created_at),
        thresholds={"slow_ms": slow_ms},
    )
    typer.echo(f"report written -> {out}")

if __name__ == "__main__":
    app()
import typer
from core import parser as core_parser
from engines.contract import generator as contract_gen
from apps.runner.http_runner import send_request
from apps.reporting.renderers.datafuzz import render_report
import json
import pathlib
import typer
import asyncio

# persistence
from storage.db import init_db
from storage.repository import create_run, save_result, get_latest_run, get_results_for_run

# async runner
from apps.runner.async_runner import run_concurrent

app = typer.Typer()

@app.command()
def gen(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    n: int = typer.Option(10, "--n", help="Number of samples"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock")
):
    # TODO: agregar soporte para generar payloads para múltiples endpoints en paralelo
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, "post")
    samples = [contract_gen.gen_valid_payload(schema) for _ in range(n)]
    out = pathlib.Path("reports/samples").resolve()
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "payloads.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f"generated {len(samples)} payloads -> {out / 'payloads.json'}")

@app.command()
def run(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    method: str = typer.Option("post", "--method", "-m", help="HTTP method"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock"),
    run_name: str | None = typer.Option(None, "--name", "-n", help="Optional run name")
):
    # FIXME: el manejo de errores de conexión necesita mejoras
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, method)

    # generate valid payload + invalid mutations from generator
    valid = contract_gen.gen_valid_payload(schema)
    muts = contract_gen.gen_invalid_mutations(schema)  # list of (name, payload)

    cases = [("valid", valid)] + muts
    url = base_url.rstrip("/") + endpoint

    run_obj = create_run(name=run_name)
    items = []

    for idx, (case_name, payload) in enumerate(cases, start=1):
        resp = send_request(method, url, json_body=payload)
        # persist
        save_result(
            run_id=run_obj.id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            status_code=resp.get("status_code"),
            latency=resp.get("latency"),
            error=resp.get("error"),
        )

        # map result/result string
        status = resp.get("status_code")
        latency_ms = None if resp.get("latency") is None else round(resp["latency"] * 1000, 1)

        if case_name == "valid":
            payload_type = "valid"
            if status and 200 <= status < 300:
                result_str = "OK"
            elif status:
                result_str = "FALLO"
            else:
                result_str = "ERROR"
            note = ""
        else:
            payload_type = "invalid"
            # tag invalid subtype in note/mutation
            mutation_name = case_name
            if status and 200 <= status < 300:
                # server accepted an invalid payload
                result_str = f"ACEPTADO (invalido:{mutation_name})"
            elif status and status >= 400:
                # server rejected invalid payload (expected)
                result_str = f"RECHAZADO (invalido:{mutation_name})"
            else:
                result_str = f"ERROR (invalido:{mutation_name})"
            note = mutation_name

        items.append({
            "id": idx,
            "payload_type": payload_type,
            "mutation": (None if case_name == "valid" else case_name),
            "status": str(status) if status is not None else "error",
            "latency_ms": latency_ms,
            "result": result_str,
            "note": note,
        })

    render_report(
        items=items,
        output_path="reports/samples/report.html",
        endpoint=endpoint,
        run_name=run_name,
        created_at=None
    )
    print(f"run complete (run_id={run_obj.id})")

@app.command()
def run_parallel(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    method: str = typer.Option("post", "--method", "-m", help="HTTP method"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock"),
    n: int = typer.Option(10, "--n", help="Number of requests to send"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Concurrency level"),
    timeout: float = typer.Option(5.0, "--timeout", help="Per-request timeout"),
    retries: int = typer.Option(1, "--retries", help="Retries per request"),
    run_name: str | None = typer.Option(None, "--name", "-n", help="Optional run name")
):
    # TODO: refactorizar esto, está medio repetitivo en algunos comandos
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, method)

    # build payload set mixing valid and invalid cases
    valid = contract_gen.gen_valid_payload(schema)
    muts = contract_gen.gen_invalid_mutations(schema)  # list of (name, payload)

    # create a list of payloads: prefer a mix (e.g., 60% valid, rest invalid cycles)
    payloads = []
    mutation_meta = []  # parallel list with metadata: ("valid", None) or ("invalid", mutation_name)
    for i in range(n):
        if muts and (i % 4 == 0):  # every 4th request use an invalid mutation (heuristic)
            name, p = muts[(i // 4) % len(muts)]
            payloads.append(p)
            mutation_meta.append(("invalid", name))
        else:
            payloads.append(valid)
            mutation_meta.append(("valid", None))

    url = base_url.rstrip("/") + endpoint
    run_obj = create_run(name=run_name)

    res = asyncio.run(run_concurrent(method, url, payloads, concurrency=concurrency, timeout=timeout, retries=retries))

    items = []
    for idx, (meta, payload, r) in enumerate(zip(mutation_meta, payloads, res["results"]), start=1):
        payload_type, mutation_name = meta
        save_result(
            run_id=run_obj.id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            status_code=r.get("status_code"),
            latency=r.get("latency"),
            error=r.get("error"),
        )

        status = r.get("status_code")
        latency_ms = None if r.get("latency") is None else round(r["latency"] * 1000, 1)

        if payload_type == "valid":
            if status and 200 <= status < 300:
                result_str = "OK"
            elif status:
                result_str = "FALLO"
            else:
                result_str = "ERROR"
            note = ""
        else:
            if status and 200 <= status < 300:
                result_str = f"ACEPTADO (invalido:{mutation_name})"
            elif status and status >= 400:
                result_str = f"RECHAZADO (invalido:{mutation_name})"
            else:
                result_str = f"ERROR (invalido:{mutation_name})"
            note = mutation_name

        items.append({
            "id": idx,
            "payload_type": payload_type,
            "mutation": mutation_name,
            "status": str(status) if status is not None else "error",
            "latency_ms": latency_ms,
            "result": result_str,
            "note": note,
        })

    render_report(
        items=items,
        output_path="reports/samples/report.html",
        endpoint=endpoint,
        run_name=run_name,
        created_at=None
    )
    print("run-parallel complete")
    print(json.dumps(res["summary"], indent=2, ensure_ascii=False))

@app.command()
def report(
    name: str | None = typer.Option(None, "--name", "-n", help="Optional run name to filter latest run"),
    out: str = typer.Option("reports/samples/report.html", "--out", help="Output HTML path"),
    slow_ms: int = typer.Option(900, "--slow-ms", help="Threshold for 'slow' classification in ms"),
):
    init_db()
    run_obj = get_latest_run(name=name)
    if not run_obj:
        typer.echo("No runs found. Execute a run first.")
        raise typer.Exit(code=1)

    results = get_results_for_run(run_obj.id)
    if not results:
        typer.echo("Selected run has no results.")
        raise typer.Exit(code=1)

    # Transform DB rows to items expected by render_report
    items = []
    for idx, r in enumerate(results, start=1):
        status = r.status_code
        latency_ms = None if r.latency is None else round(r.latency * 1000, 1)
        payload_type = "valid"  # default; we don't persist mutation type yet
        # We keep 'note' with error text or blank
        items.append({
            "id": idx,
            "payload_type": payload_type,
            "mutation": None,
            "status": str(status) if status is not None else "error",
            "latency_ms": latency_ms,
            "result": "",  # will be recomputed by renderer normalization
            "note": r.error or "",
        })

    render_report(
        items=items,
        output_path=out,
        endpoint=results[0].endpoint,
        run_name=run_obj.name,
        created_at=str(run_obj.created_at),
        thresholds={"slow_ms": slow_ms},
    )
    typer.echo(f"report written -> {out}")

if __name__ == "__main__":
    app()