from storage.db import SessionLocal
from storage.models import Run, Result
from typing import Optional, List

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


def get_latest_run(name: Optional[str] = None) -> Optional[Run]:
    """Return the most recent Run, optionally filtered by name."""
    session = SessionLocal()
    try:
        q = session.query(Run)
        if name:
            q = q.filter(Run.name == name)
        q = q.order_by(Run.created_at.desc())
        return q.first()
    finally:
        session.close()


def get_results_for_run(run_id: int) -> List[Result]:
    """Return all Result rows for a run id, ordered by id ascending."""
    session = SessionLocal()
    try:
        q = (
            session.query(Result)
            .filter(Result.run_id == run_id)
            .order_by(Result.id.asc())
        )
        return list(q.all())
    finally:
        session.close()