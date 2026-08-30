"""Tests that a .env file is actually loaded.

.env.example ships with the project and python-dotenv was already a declared
dependency, but nothing imported it, so the file was read by no one. Anyone
setting DATABASE_PATH there would have seen the pipeline keep writing to the
default location without any hint why.

These tests run in a subprocess with a temporary working directory, because
load_dotenv runs at import time and os.environ cannot be un-imported between
test cases.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Import main so the .env is loaded, then report the path the database module
# settled on.
PROBE = "import main; import db.database as d; print('PATH=' + d.DATABASE_PATH)"


def _run_probe(cwd: Path, env: dict[str, str] | None = None) -> str:
    full_env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    full_env.pop("DATABASE_PATH", None)
    if env:
        full_env.update(env)

    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    for line in result.stdout.splitlines():
        if line.startswith("PATH="):
            return line.partition("=")[2]
    raise AssertionError(f"probe printed no PATH line: {result.stdout!r}")


class TestDotenvLoading:
    def test_env_file_is_read(self, tmp_path):
        """DATABASE_PATH from .env reaches db.database."""
        (tmp_path / ".env").write_text("DATABASE_PATH=from-the-env-file.db\n")
        assert _run_probe(tmp_path) == "from-the-env-file.db"

    def test_default_applies_without_env_file(self, tmp_path):
        """Without a .env the built-in default is used."""
        assert _run_probe(tmp_path) == "output/shopflow.db"

    def test_real_environment_wins_over_env_file(self, tmp_path):
        """An exported variable overrides the file."""
        (tmp_path / ".env").write_text("DATABASE_PATH=from-the-env-file.db\n")
        assert (
            _run_probe(tmp_path, {"DATABASE_PATH": "from-the-environment.db"})
            == "from-the-environment.db"
        )
