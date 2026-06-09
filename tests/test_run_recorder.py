"""Tests for the ETL pipeline run recorder."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from agents import run_recorder
from agents.orchestrator import PipelineOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"


@pytest.fixture(scope="module")
def ensure_sample_data():
    """Generate sample CSV/JSON inputs once if they are not already present.

    Mirrors the auto-build that the Streamlit app does on first start so
    integration tests are self-sufficient on CI.
    """
    if RAW_DATA_DIR.exists() and any(RAW_DATA_DIR.iterdir()):
        return
    generator = REPO_ROOT / "data" / "generate_sample_data.py"
    subprocess.run(
        [sys.executable, str(generator)],
        cwd=REPO_ROOT,
        check=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )


class TestStartFinish:
    def test_start_returns_id_and_creates_running_row(self, db_path):
        run_id = run_recorder.start_run(db_path, mode="full")
        assert run_id == 1

        runs = run_recorder.list_runs(db_path)
        assert len(runs) == 1
        assert runs[0]["run_id"] == 1
        assert runs[0]["status"] == "running"
        assert runs[0]["mode"] == "full"
        assert runs[0]["started_at"] is not None
        assert runs[0]["finished_at"] is None

    def test_finish_success_updates_row(self, db_path):
        run_id = run_recorder.start_run(db_path, mode="incremental")
        run_recorder.finish_run(
            db_path,
            run_id,
            status="success",
            quality_score=97.5,
            phase_timings={"extract": 0.4, "load": 0.2},
            row_counts={"fact_sales": 12345},
        )

        runs = run_recorder.list_runs(db_path)
        row = runs[0]
        assert row["status"] == "success"
        assert row["quality_score"] == 97.5
        assert row["phase_timings"] == {"extract": 0.4, "load": 0.2}
        assert row["row_counts"] == {"fact_sales": 12345}
        assert row["finished_at"] is not None
        assert row["duration_seconds"] is not None
        assert row["duration_seconds"] >= 0

    def test_finish_failure_records_error(self, db_path):
        run_id = run_recorder.start_run(db_path)
        run_recorder.finish_run(
            db_path,
            run_id,
            status="failed",
            error_message="Source file missing: orders.csv",
        )

        row = run_recorder.list_runs(db_path)[0]
        assert row["status"] == "failed"
        assert "orders.csv" in row["error_message"]

    def test_finish_unknown_run_is_silent(self, db_path):
        # Should not raise even if the run_id doesn't exist
        run_recorder.finish_run(db_path, 9999, status="success")
        assert run_recorder.list_runs(db_path) == []


class TestListRuns:
    def test_returns_most_recent_first(self, db_path):
        ids = [run_recorder.start_run(db_path) for _ in range(3)]
        runs = run_recorder.list_runs(db_path)
        assert [r["run_id"] for r in runs] == list(reversed(ids))

    def test_respects_limit(self, db_path):
        for _ in range(5):
            run_recorder.start_run(db_path)
        runs = run_recorder.list_runs(db_path, limit=2)
        assert len(runs) == 2

    def test_empty_table_returns_empty_list(self, db_path):
        assert run_recorder.list_runs(db_path) == []


class TestOrchestratorIntegration:
    """The full pipeline must persist exactly one run record on success."""

    def test_successful_run_records_one_row(self, db_path, ensure_sample_data):
        orc = PipelineOrchestrator(data_dir="data", db_path=db_path, mode="full")
        orc.run()

        runs = run_recorder.list_runs(db_path)
        assert len(runs) == 1
        row = runs[0]
        assert row["status"] == "success"
        assert row["duration_seconds"] is not None
        assert row["quality_score"] is not None
        assert set(row["phase_timings"].keys()) == {
            "extract",
            "validate",
            "transform",
            "build_dimensions",
            "load",
            "analyze",
        }

    def test_failed_run_records_failure(self, db_path, monkeypatch):
        # Force the extract phase to throw
        from agents import orchestrator

        def boom(*_args, **_kwargs):
            raise RuntimeError("simulated extract failure")

        monkeypatch.setattr(orchestrator, "extract_all", boom)

        orc = PipelineOrchestrator(data_dir="data", db_path=db_path, mode="full")
        with pytest.raises(RuntimeError, match="simulated extract failure"):
            orc.run()

        runs = run_recorder.list_runs(db_path)
        assert len(runs) == 1
        assert runs[0]["status"] == "failed"
        assert "simulated extract failure" in runs[0]["error_message"]
