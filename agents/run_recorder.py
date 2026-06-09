"""Pipeline run recorder — persists one row in etl_runs per orchestrator run.

The orchestrator calls ``start_run`` before phase 1 and ``finish_run``
once the pipeline either completes or fails. The recorder is best-effort:
errors here must not bring the pipeline down, so callers should still
record a failure even when the database is unavailable for inserts.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from db.database import Base, get_engine
from db.orm_models import ETLRunTable


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _session(db_path: str):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine, tables=[ETLRunTable.__table__])
    Session = sessionmaker(bind=engine)
    return Session(), engine


def start_run(db_path: str, mode: str = "full") -> int:
    """Insert a row in 'running' state and return its run_id."""
    session, _ = _session(db_path)
    try:
        run = ETLRunTable(
            started_at=_utc_now(),
            mode=mode,
            status="running",
        )
        session.add(run)
        session.commit()
        return run.run_id
    finally:
        session.close()


def finish_run(
    db_path: str,
    run_id: int,
    *,
    status: str,
    error_message: str | None = None,
    quality_score: float | None = None,
    phase_timings: dict | None = None,
    row_counts: dict | None = None,
) -> None:
    """Update the run record with final state. Silent if the row is missing."""
    session, _ = _session(db_path)
    try:
        run = session.get(ETLRunTable, run_id)
        if run is None:
            return
        finished = _utc_now()
        run.finished_at = finished
        run.duration_seconds = (finished - run.started_at).total_seconds()
        run.status = status
        run.error_message = error_message
        run.quality_score = quality_score
        run.phase_timings = phase_timings
        run.row_counts = row_counts
        session.commit()
    finally:
        session.close()


def list_runs(db_path: str, limit: int = 50) -> list[dict]:
    """Return the most-recent runs as plain dicts for the UI."""
    session, _ = _session(db_path)
    try:
        rows = session.query(ETLRunTable).order_by(ETLRunTable.run_id.desc()).limit(limit).all()
        return [
            {
                "run_id": r.run_id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "duration_seconds": r.duration_seconds,
                "mode": r.mode,
                "status": r.status,
                "error_message": r.error_message,
                "quality_score": r.quality_score,
                "phase_timings": r.phase_timings or {},
                "row_counts": r.row_counts or {},
            }
            for r in rows
        ]
    finally:
        session.close()
