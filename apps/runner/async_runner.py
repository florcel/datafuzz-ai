import asyncio
import time
import math
from typing import List, Dict, Any
import httpx

async def _send_single(client: httpx.AsyncClient, method: str, url: str, json_body, timeout: float, retries: int):
    attempt = 0
    last_exc = None
    method = method.upper()
    while attempt <= retries:
        try:
            t0 = time.perf_counter()
            r = await client.request(method, url, json=json_body, timeout=timeout)
            latency = time.perf_counter() - t0
            return {"status_code": r.status_code, "latency": latency, "body": r.text}
        except Exception as e:
            last_exc = e
            attempt += 1
    return {"status_code": None, "latency": None, "error": str(last_exc)}

async def _worker(semaphore: asyncio.Semaphore, client: httpx.AsyncClient, method: str, url: str, payload, timeout: float, retries: int):
    async with semaphore:
        return await _send_single(client, method, url, payload, timeout, retries)

def _percentile(sorted_vals: List[float], p: float):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d = k - f
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * d

async def run_concurrent(method: str, url: str, payloads: List[Dict[str, Any]], concurrency: int = 10, timeout: float = 5.0, retries: int = 2):
    # manda todo en paralelo con semaforo para no saturar
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(_worker(semaphore, client, method, url, payload, timeout, retries))
            for payload in payloads
        ]
        for task in asyncio.as_completed(tasks):
            res = await task
            results.append(res)

    # metrics
    latencies = [r["latency"] for r in results if r.get("latency") is not None]
    sorted_lat = sorted(latencies)
    summary = {
        "total": len(results),
        "successful": sum(1 for r in results if r.get("status_code") and 200 <= r.get("status_code") < 300),
        "errors": sum(1 for r in results if not r.get("status_code")),
        "statuses": {},
        "percentiles": {
            "p50": _percentile(sorted_lat, 50),
            "p95": _percentile(sorted_lat, 95),
            "p99": _percentile(sorted_lat, 99),
        },
    }
    # status counts
    for r in results:
        sc = r.get("status_code")
        key = str(sc) if sc is not None else "error"
        summary["statuses"].setdefault(key, 0)
        summary["statuses"][key] += 1

    return {"summary": summary, "results": results}
import asyncio
import time
import math
from typing import List, Dict, Any
import httpx

async def _send_single(client: httpx.AsyncClient, method: str, url: str, json_body, timeout: float, retries: int):
    attempt = 0
    last_exc = None
    method = method.upper()
    while attempt <= retries:
        try:
            t0 = time.perf_counter()
            r = await client.request(method, url, json=json_body, timeout=timeout)
            latency = time.perf_counter() - t0
            return {"status_code": r.status_code, "latency": latency, "body": r.text}
        except Exception as e:
            last_exc = e
            attempt += 1
    return {"status_code": None, "latency": None, "error": str(last_exc)}

async def _worker(semaphore: asyncio.Semaphore, client: httpx.AsyncClient, method: str, url: str, payload, timeout: float, retries: int):
    async with semaphore:
        return await _send_single(client, method, url, payload, timeout, retries)

def _percentile(sorted_vals: List[float], p: float):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d = k - f
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * d

async def run_concurrent(method: str, url: str, payloads: List[Dict[str, Any]], concurrency: int = 10, timeout: float = 5.0, retries: int = 2):
    # manda todo en paralelo con semaforo para no saturar
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(_worker(semaphore, client, method, url, payload, timeout, retries))
            for payload in payloads
        ]
        for task in asyncio.as_completed(tasks):
            res = await task
            results.append(res)

    # metrics
    latencies = [r["latency"] for r in results if r.get("latency") is not None]
    sorted_lat = sorted(latencies)
    summary = {
        "total": len(results),
        "successful": sum(1 for r in results if r.get("status_code") and 200 <= r.get("status_code") < 300),
        "errors": sum(1 for r in results if not r.get("status_code")),
        "statuses": {},
        "percentiles": {
            "p50": _percentile(sorted_lat, 50),
            "p95": _percentile(sorted_lat, 95),
            "p99": _percentile(sorted_lat, 99),
        },
    }
    # status counts
    for r in results:
        sc = r.get("status_code")
        key = str(sc) if sc is not None else "error"
        summary["statuses"].setdefault(key, 0)
        summary["statuses"][key] += 1

    return {"summary": summary, "results": results}