from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_NAME = "datafuzz_report.html"

# --------- NUEVO: helpers de normalización y clasificación ---------
def _safe_int(value, default=None):
    try:
        v = int(value)
        return v
    except Exception:
        return default

def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default

def _classify_result(payload_type: str, status: Optional[int], latency_ms: Optional[float], slow_ms: int) -> str:
    # sin status -> lo tratamos como fallo del lado del servidor para válidos,
    # para inválidos lo consideramos 'OK (esperado)'
    if status is None:
        return "FALLO" if payload_type == "valid" else "OK (esperado)"

    # status error HTTP (4xx/5xx)
    if status >= 400:
        return "OK (esperado)" if payload_type == "invalid" else "FALLO"

    # status exitoso (2xx/3xx)
    if latency_ms is not None and latency_ms >= slow_ms:
        return "LENTO"
    return "OK"

def _normalize_items(items: List[Dict[str, Any]], slow_ms: int) -> List[Dict[str, Any]]:
    norm = []
    for it in items:
        payload_type = "valid" if str(it.get("payload_type", "")).lower().startswith("val") else "invalid"

        raw_status = it.get("status")
        # admitir "error" como fallo sin código
        status = None
        if raw_status is not None and str(raw_status).lower() != "error":
            status = _safe_int(raw_status, default=None)

        latency_ms = _safe_float(it.get("latency_ms"), default=None)

        result = _classify_result(payload_type, status, latency_ms, slow_ms)

        norm.append({
            "id": it.get("id"),
            "payload_type": payload_type,
            "status": status if status is not None else "error",
            "latency_ms": None if latency_ms is None else int(latency_ms),
            "result": result,
            "note": it.get("note") or "",
        })
    return norm
# -------------------------------------------------------------------

def _compute_totals(items: List[Dict[str, Any]], thresholds: Dict[str, int]) -> Dict[str, Any]:
    total = len(items)
    valid_ok = sum(1 for it in items if it.get("payload_type") == "valid" and it.get("result") == "OK")
    invalid_expected_ok = sum(1 for it in items if it.get("payload_type") == "invalid" and "OK" in str(it.get("result")))
    accepted_invalid = sum(1 for it in items if it.get("payload_type") == "invalid" and it.get("result") == "FALLO")

    numeric_latencies = [float(it.get("latency_ms")) for it in items if isinstance(it.get("latency_ms"), (int, float))]
    slow_threshold = int(thresholds.get("slow_ms", 900))
    slow = sum(1 for v in numeric_latencies if v >= slow_threshold)

    # if there are no numeric latencies, set avg to None and mark has_latency=False
    if numeric_latencies:
        avg_latency = round(sum(numeric_latencies) / len(numeric_latencies), 1)
        has_latency = True
    else:
        avg_latency = None
        has_latency = False

    return {
        "total": total,
        "valid_ok": valid_ok,
        "invalid_expected_ok": invalid_expected_ok,
        "accepted_invalid": accepted_invalid,
        "slow": slow,
        "avg_latency_ms": avg_latency,
        "has_latency": has_latency,
    }

def render_report(
    items: List[Dict[str, Any]],
    output_path: str,
    endpoint: str = "/users",
    run_name: Optional[str] = None,
    created_at: Optional[str] = None,
    thresholds: Optional[Dict[str, int]] = None,
    title: str = "Datafuzz-ai — Reporte",
    header: str = "Reporte — Datafuzz-ai",
    template_dir: Optional[str] = None,
    template_name: str = TEMPLATE_NAME,
    footer_note: Optional[str] = "Reporte generado por Datafuzz-ai"
) -> str:
    thresholds = thresholds or {"slow_ms": 900}
    slow_ms = int(thresholds.get("slow_ms", 900))

    # normalizamos y clasificamos antes de computar totales
    normalized_items = _normalize_items(items, slow_ms)
    totals = _compute_totals(normalized_items, thresholds)

    # default template dir: apps/reporting/templates (dos niveles arriba)
    if template_dir:
        templates_path = Path(template_dir)
    else:
        templates_path = Path(__file__).parents[1] / "templates"

    env = Environment(
        loader=FileSystemLoader(str(templates_path)),
        autoescape=select_autoescape(["html", "xml"])
    )
    tmpl = env.get_template(template_name)

    html = tmpl.render(
        title=title,
        header=header,
        endpoint=endpoint,
        run_name=run_name,
        created_at=created_at or datetime.now().strftime("%Y-%m-%d %H:%M"),
        totals=totals,
        thresholds=thresholds,
        items=normalized_items,   # ← usamos los normalizados
        footer_note=footer_note,
    )

    out = Path(output_path)
    if out.parent.exists() and not out.parent.is_dir():
        out.parent.rename(out.parent.with_name(out.parent.name + ".bak"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)