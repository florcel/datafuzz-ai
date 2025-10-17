from storage.db import SessionLocal
from storage.models import Run, Result

def create_run(name: str | None = None):
    session = SessionLocal()
    try:
        r = Run(name=name)
        session.add(r)
        session.commit()
        session.refresh(r)
        return r
    finally:
        session.close()

def save_result(run_id: int, endpoint: str, method: str, payload, status_code, latency, error):
    session = SessionLocal()
    try:
        res = Result(
            run_id=run_id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            status_code=status_code,
            latency=latency,
            error=error,
        )
        session.add(res)
        session.commit()
        session.refresh(res)
        return res
    finally:
        session.close()