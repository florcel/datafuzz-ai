# apps/core/runner.py
import time, httpx
from statistics import median

def _pctl(values, q):
    if not values: return 0
    values = sorted(values)
    idx = max(0, min(len(values)-1, int(len(values)*q)-1))
    return values[idx]

def run_payloads(base_url: str, path: str, method: str, payloads: list[dict]) -> dict:
    lat, errors, codes = [], 0, {}
    for data in payloads:
        t0 = time.perf_counter()
        if method == "get":
            r = httpx.get(base_url + path, params=data, timeout=5.0)
        else:
            r = httpx.request(method.upper(), base_url + path, json=data, timeout=5.0)
        dt = (time.perf_counter() - t0) * 1000
        lat.append(dt)
        codes[r.status_code] = codes.get(r.status_code, 0) + 1
        if r.status_code >= 500:
            errors += 1
    return {
        "total": len(payloads),
        "errors": errors,
        "status_dist": codes,
        "latency_ms_p50": _pctl(lat, 0.50),
        "latency_ms_p95": _pctl(lat, 0.95),
    }
