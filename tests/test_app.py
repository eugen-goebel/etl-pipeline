"""Tests for the Streamlit dashboard layer (app.py).

The dashboard was the only untested layer and is where the cold-start
race condition lived, so these tests cover exactly that surface: the
app boots and renders, and concurrent demo builds cannot corrupt the
database (regression test for the duplicate-key crash on Streamlit
Cloud).
"""

import os
import sqlite3
import subprocess
import sys
import threading
import uuid

import pytest
from streamlit.testing.v1 import AppTest

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(REPO_DIR, "app.py")


def _generate_raw_data():
    """Run the sample data generator (idempotent, writes data/raw)."""
    generator = os.path.join(REPO_DIR, "data", "generate_sample_data.py")
    subprocess.run([sys.executable, generator], check=True, cwd=REPO_DIR)


class TestDataVersionGuard:
    """The demo DB must rebuild when it predates the current DATA_VERSION."""

    def test_is_current_only_when_version_matches(self, tmp_path, monkeypatch):
        import app

        db = tmp_path / "shopflow.db"
        version = tmp_path / "shopflow.db.version"
        monkeypatch.setattr(app, "DB_PATH", str(db))
        monkeypatch.setattr(app, "VERSION_PATH", str(version))

        # No database yet
        assert not app._demo_db_is_current()

        # Database exists but no version marker (old build)
        db.write_text("")
        assert not app._demo_db_is_current()

        # Version marker from an older data version
        version.write_text("1")
        assert not app._demo_db_is_current()

        # Version marker matches the current data version
        version.write_text(app.DATA_VERSION)
        assert app._demo_db_is_current()


class TestAppSmoke:
    def test_boots_and_renders_executive_overview(self):
        """The dashboard starts in demo mode and renders without errors."""
        at = AppTest.from_file(APP_PATH, default_timeout=180)
        at.run()

        assert not at.exception

        metric_labels = {m.label for m in at.metric}
        assert "Total Revenue" in metric_labels
        assert "Total Orders" in metric_labels

    def test_count_metrics_render_as_integers(self):
        """Counts must not render with a trailing .0 (e.g. '11,429.0')."""
        at = AppTest.from_file(APP_PATH, default_timeout=180)
        at.run()

        by_label = {m.label: str(m.value) for m in at.metric}
        assert not by_label["Total Orders"].endswith(".0")
        assert not by_label["Unique Customers"].endswith(".0")


class TestConcurrentDemoBuild:
    def test_parallel_builds_leave_a_valid_database(self, tmp_path):
        """Regression for the cold-start race on Streamlit Cloud.

        Two sessions used to build the demo database into the same file at
        the same time, and the second INSERT wave crashed with a UNIQUE
        constraint error. The fix builds into a unique temporary file and
        atomically renames it into place, so parallel builds must both
        succeed and leave a complete database.
        """
        from agents.orchestrator import PipelineOrchestrator

        _generate_raw_data()
        db_path = str(tmp_path / "shopflow.db")
        errors = []

        def build():
            try:
                tmp_db = f"{db_path}.{uuid.uuid4().hex}.tmp"
                PipelineOrchestrator(
                    data_dir=os.path.join(REPO_DIR, "data"),
                    db_path=tmp_db,
                    mode="full",
                ).run()
                os.replace(tmp_db, db_path)
            except Exception as exc:  # noqa: BLE001 - collected for the assert
                errors.append(exc)

        threads = [threading.Thread(target=build) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        rows = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM dim_product").fetchone()[0]
        assert rows == 300

    def test_build_demo_db_is_wrapped_in_cache_resource(self):
        """ensure_demo_db must stay cached so it runs once per process."""
        pytest.importorskip("streamlit")
        import app

        # st.cache_resource-wrapped functions expose a clear() method
        assert hasattr(app.ensure_demo_db, "clear")
