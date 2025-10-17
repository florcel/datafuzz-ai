import time
import httpx

def send_request(method: str, url: str, json_body=None, timeout: float = 5.0, retries: int = 2):
    attempt = 0
    last_exc = None
    method = method.upper()
    while attempt <= retries:
        try:
            t0 = time.time()
            r = httpx.request(method, url, json=json_body, timeout=timeout)
            latency = time.time() - t0
            return {"status_code": r.status_code, "latency": latency, "body": r.text}
        except Exception as e:
            last_exc = e
            attempt += 1
    return {"status_code": None, "latency": None, "error": str(last_exc)}