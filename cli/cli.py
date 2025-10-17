import typer, json, os
from pathlib import Path
from apps.core.openapi import load_spec, find_endpoint
from apps.engines.contract import make_payloads
from apps.core.runner import run_payloads
from apps.reporting.renderers.html import render_latest

app = typer.Typer(add_completion=False)

@app.command()
def gen(
    spec: str = typer.Option(..., help="Ruta a openapi.yaml"),
    endpoint: str = typer.Option(..., help="Path del endpoint, ej: /users"),
    method: str = typer.Option("post", help="get/post/put/delete"),
    n: int = typer.Option(50, help="Cantidad de payloads"),
    base_url: str = typer.Option(..., help="URL base del mock o staging"),
):
    s = load_spec(spec)
    ep = find_endpoint(s, endpoint, method)
    payloads = make_payloads(ep.schema, n=n)
    summary = run_payloads(base_url, endpoint, method, payloads)

    os.makedirs("reports/latest", exist_ok=True)
    Path("reports/latest/summary.json").write_text(json.dumps(summary, indent=2))
    render_latest()

if __name__ == "__main__":
    app()
