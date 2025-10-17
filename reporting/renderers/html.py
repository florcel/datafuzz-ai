# apps/reporting/renderers/html.py
import json, os
from jinja2 import Template

TPL = Template("""
<!doctype html><html><head><meta charset="utf-8"><title>DataFuzz Report</title>
<style>body{font-family:Inter,system-ui,Arial;margin:24px} .k{display:flex;gap:12px}</style>
</head><body>
<h1>DataFuzz Report</h1>
<div class="k">
  <div><b>Total</b>: {{ s.total }}</div>
  <div><b>Errors 5xx</b>: {{ s.errors }}</div>
  <div><b>P50</b>: {{ s.latency_ms_p50|round(2) }} ms</div>
  <div><b>P95</b>: {{ s.latency_ms_p95|round(2) }} ms</div>
</div>
<h3>Status codes</h3>
<ul>
{% for code, cnt in s.status_dist.items() %}
  <li>{{ code }}: {{ cnt }}</li>
{% endfor %}
</ul>
</body></html>
""")

def render_latest():
    os.makedirs("reports/latest", exist_ok=True)
    s = json.load(open("reports/latest/summary.json", "r", encoding="utf-8"))
    open("reports/latest/index.html", "w", encoding="utf-8").write(TPL.render(s=s))
