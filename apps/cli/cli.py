import typer
from core import parser as core_parser
from engines.contract import generator as contract_gen
from apps.runner.http_runner import send_request
from apps.reporting.renderers.html import render_latest
import json
import pathlib

# persistence
from storage.db import init_db
from storage.repository import create_run, save_result

# async runner
from apps.runner.async_runner import run_concurrent
import asyncio

app = typer.Typer()

@app.command()
def gen(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to OpenAPI spec"),
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="API endpoint (e.g. /users)"),
    n: int = typer.Option(10, "--n", help="Number of samples"),
    base_url: str = typer.Option("http://localhost:4010", "--base-url", help="Base URL for mock")
):
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
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, method)
    valid = contract_gen.gen_valid_payload(schema)
    url = base_url.rstrip("/") + endpoint
    resp = send_request(method, url, json_body=valid)

    # persist run + result
    run_obj = create_run(name=run_name)
    save_result(
        run_id=run_obj.id,
        endpoint=endpoint,
        method=method,
        payload=valid,
        status_code=resp.get("status_code"),
        latency=resp.get("latency"),
        error=resp.get("error"),
    )

    render_latest([{"endpoint": endpoint, "method": method, **resp}])
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
    """Generate N payloads and execute them concurrently, persist results and render report."""
    init_db()
    spec_obj = core_parser.load_spec(spec)
    schema = core_parser.get_schema_for_path(spec_obj, endpoint, method)
    payloads = [contract_gen.gen_valid_payload(schema) for _ in range(n)]
    url = base_url.rstrip("/") + endpoint

    # create DB run
    run_obj = create_run(name=run_name)

    # execute async
    res = asyncio.run(run_concurrent(method, url, payloads, concurrency=concurrency, timeout=timeout, retries=retries))

    # persist each result
    for payload, r in zip(payloads, res["results"]):
        save_result(
            run_id=run_obj.id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            status_code=r.get("status_code"),
            latency=r.get("latency"),
            error=r.get("error"),
        )

    # render and print summary
    render_latest([{"endpoint": endpoint, "method": method, **r} for r in res["results"]])
    print("run-parallel complete")
    print(json.dumps(res["summary"], indent=2, ensure_ascii=False))

@app.command()
def report():
    print("open reports/samples/report.html")

if __name__ == "__main__":
    app()