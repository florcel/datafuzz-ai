from jinja2 import Environment, FileSystemLoader
import json
import pathlib

TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

def render_latest(results: list, out_path="reports/samples/report.html"):
    tpl = env.get_template("summary.html")
    html = tpl.render(results=results)
    parent = pathlib.Path(out_path).parent
    # if a file exists where we need a directory, rename it to .bak to avoid FileExistsError
    if parent.exists() and not parent.is_dir():
        backup = parent.with_name(parent.name + ".bak")
        parent.rename(backup)
    parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path